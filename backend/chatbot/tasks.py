"""
chatbot/tasks.py

Celery tasks for the RAG pipeline:

  index_product_chunks  — triggered by Product post_save signal
  rebuild_rag_index     — nightly Celery Beat job (full ChromaDB rebuild)
  run_ragas_evaluation  — offline thesis evaluation task
"""

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

# Character window for each chunk with 64-char overlap
CHUNK_SIZE    = 1500
CHUNK_OVERLAP = 200


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character-level chunks."""
    if len(text) <= size:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


def _build_product_text(product) -> list[tuple[str, str]]:
    """
    Build (text, source_type) pairs for a product.
    Returns multiple chunks per product covering different aspects.
    """
    from chatbot.models import RAGDocument

    chunks = []

    # Chunk 1: Core metadata
    meta = (
        f"Product: {product.title}\n"
        f"Artist: {product.artist.name}\n"
        f"Style: {product.style}\n"
        f"Color: {product.color}\n"
        f"Composition: {product.composition}\n"
        f"Price: £{product.price}\n"
        f"Available sizes: {', '.join(s.size for s in product.sizes.filter(stock__gt=0))}\n"
        f"Status: {'In stock' if not product.is_sold_out else 'Sold out'}\n"
        f"Deadline: {product.deadline.strftime('%d %b %Y')}"
    )
    chunks.append((meta, RAGDocument.SourceType.PRODUCT_METADATA))

    # Chunk 2+: Split composition/description if long
    if len(product.composition) > 300:
        for part in _chunk_text(product.composition):
            chunks.append((
                f"Product: {product.title}\nDetails: {part}",
                RAGDocument.SourceType.PRODUCT_METADATA,
            ))

    return chunks


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    queue="ml",
    name="chatbot.index_product_chunks",
)
def index_product_chunks(self, product_id: str) -> dict:
    """
    Generate RAG chunks for a single product and upsert into:
      1. RAGDocument table (for BM25 retrieval)
      2. ChromaDB (for dense retrieval)
    """
    try:
        from sentence_transformers import SentenceTransformer

        from chatbot.models import RAGDocument
        from core.models import Product
        from ml.rag_pipeline import _get_chroma_collection

        product = Product.objects.select_related("artist").prefetch_related("sizes").get(
            product_id=product_id
        )

        model = SentenceTransformer("all-MiniLM-L6-v2")
        collection = _get_chroma_collection()
        chunk_pairs = _build_product_text(product)

        created_count = updated_count = 0

        for idx, (text, source_type) in enumerate(chunk_pairs):
            vector = model.encode(text, normalize_embeddings=True).tolist()

            obj, created = RAGDocument.objects.update_or_create(
                product=product,
                source_type=source_type,
                chunk_index=idx,
                defaults={
                    "text":            text,
                    "vector":          vector,
                    "vector_dim":      len(vector),
                    "embedding_model": "all-MiniLM-L6-v2",
                    "is_indexed":      True,
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

            # Upsert into ChromaDB
            if collection is not None:
                doc_id = f"{product_id}_{source_type}_{idx}"
                collection.upsert(
                    ids=[doc_id],
                    documents=[text],
                    embeddings=[vector],
                    metadatas=[{
                        "doc_id":      str(obj.id),
                        "product_id":  str(product_id),
                        "source_type": source_type,
                        "chunk_index": idx,
                        "product_title": product.title,
                    }],
                )

        logger.info(
            "RAG indexed product %s: %d created, %d updated",
            product_id, created_count, updated_count,
        )
        return {"product_id": product_id, "created": created_count, "updated": updated_count}

    except Exception as exc:
        logger.error("RAG indexing failed for product %s: %s", product_id, exc)
        raise self.retry(exc=exc)


@shared_task(
    queue="ml",
    name="chatbot.rebuild_rag_index",
)
def rebuild_rag_index() -> dict:
    """
    Nightly full rebuild of the RAG index.
    Queues index_product_chunks for every active product.
    Also rebuilds the ChromaDB collection from scratch to remove stale entries.
    Runs at 4 AM UTC via Celery Beat.
    """
    import chromadb
    from django.conf import settings

    from core.models import Product

    logger.info("Starting full RAG index rebuild...")

    # Wipe and recreate ChromaDB collection
    try:
        persist_dir = getattr(settings, "CHROMA_PERSIST_DIR", "/app/chroma_db")
        client = chromadb.PersistentClient(path=persist_dir)
        try:
            client.delete_collection("fashion_rag")
        except Exception:
            pass
        client.get_or_create_collection(
            name="fashion_rag",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection reset.")
    except Exception as exc:
        logger.error("ChromaDB reset failed: %s", exc)

    # Reset is_indexed flag so all docs get reprocessed
    from chatbot.models import RAGDocument
    RAGDocument.objects.all().update(is_indexed=False)

    product_ids = list(Product.objects.values_list("product_id", flat=True))
    for pid in product_ids:
        index_product_chunks.delay(str(pid))

    logger.info("RAG rebuild queued for %d products", len(product_ids))
    return {"queued": len(product_ids)}


@shared_task(
    queue="ml",
    name="chatbot.run_ragas_evaluation",
)
def run_ragas_evaluation(session_ids: list[str] | None = None) -> dict:
    """
    Offline RAGAS evaluation task for thesis metrics.

    Computes faithfulness, answer_relevance, and context_precision
    for ChatMessage rows that have retrieved_chunks but no RAGAS scores yet.

    Can be run on specific session_ids or all unevaluated messages.
    Called manually during thesis evaluation: not scheduled by Beat.
    """
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, context_precision, faithfulness

        from chatbot.models import ChatMessage

        qs = ChatMessage.objects.filter(
            role="assistant",
            faithfulness__isnull=True,
        ).exclude(retrieved_chunks=[])

        if session_ids:
            qs = qs.filter(session__id__in=session_ids)

        messages = list(qs.select_related("session")[:200])

        if not messages:
            return {"evaluated": 0, "reason": "no_unevaluated_messages"}

        data = {
            "question":  [m.session.messages.filter(role="user").order_by("-created_at").values_list("content", flat=True).first() or "" for m in messages],
            "answer":    [m.content for m in messages],
            "contexts":  [[c["text"] for c in m.retrieved_chunks] for m in messages],
        }

        dataset = Dataset.from_dict(data)
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision],
        )

        scores_df = result.to_pandas()

        for i, msg in enumerate(messages):
            msg.faithfulness       = float(scores_df.iloc[i].get("faithfulness", 0) or 0)
            msg.answer_relevance   = float(scores_df.iloc[i].get("answer_relevancy", 0) or 0)
            msg.context_precision  = float(scores_df.iloc[i].get("context_precision", 0) or 0)

        ChatMessage.objects.bulk_update(
            messages,
            ["faithfulness", "answer_relevance", "context_precision"],
            batch_size=50,
        )

        avg_faithfulness      = scores_df["faithfulness"].mean()
        avg_answer_relevance  = scores_df["answer_relevancy"].mean()
        avg_context_precision = scores_df["context_precision"].mean()

        logger.info(
            "RAGAS evaluation complete: faithfulness=%.3f, answer_relevance=%.3f, context_precision=%.3f",
            avg_faithfulness, avg_answer_relevance, avg_context_precision,
        )

        return {
            "evaluated":          len(messages),
            "faithfulness":        round(avg_faithfulness, 4),
            "answer_relevance":    round(avg_answer_relevance, 4),
            "context_precision":   round(avg_context_precision, 4),
        }

    except Exception as exc:
        logger.error("RAGAS evaluation failed: %s", exc)
        return {"error": str(exc)}
