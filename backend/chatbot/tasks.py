"""
chatbot/tasks.py

Celery tasks for the RAG pipeline:

  index_product_chunks  — triggered by Product post_save signal
  rebuild_rag_index     — nightly Celery Beat job (full Pinecone rebuild)
  run_ragas_evaluation  — offline thesis evaluation task
"""

import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

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
    """Build (text, source_type) pairs for a product."""
    from chatbot.models import RAGDocument

    chunks = []

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

    if len(product.composition) > 300:
        for part in _chunk_text(product.composition):
            chunks.append((
                f"Product: {product.title}\nDetails: {part}",
                RAGDocument.SourceType.PRODUCT_METADATA,
            ))

    return chunks


def _get_pinecone_index():
    """Get the Pinecone index — imported here to avoid circular imports."""
    from ml.rag_pipeline import _get_pinecone_index as _get_index
    return _get_index()


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
      1. RAGDocument table  — for BM25 sparse retrieval
      2. Pinecone           — for dense vector retrieval

    Upsert semantics: safe to re-run; existing vectors are overwritten.
    """
    try:
        from sentence_transformers import SentenceTransformer

        from chatbot.models import RAGDocument
        from core.models import Product

        product = (
            Product.objects
            .select_related("artist")
            .prefetch_related("sizes")
            .get(product_id=product_id)
        )

        model      = SentenceTransformer("all-MiniLM-L6-v2")
        pc_index   = _get_pinecone_index()
        chunk_pairs = _build_product_text(product)

        created_count = updated_count = 0
        pinecone_vectors = []

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

            # Build Pinecone upsert payload
            # ID format: <product_id>_<source_type>_<chunk_index>
            pinecone_id = f"{product_id}_{source_type}_{idx}"
            pinecone_vectors.append({
                "id":     pinecone_id,
                "values": vector,
                "metadata": {
                    "doc_id":        str(obj.id),
                    "product_id":    str(product_id),
                    "source_type":   source_type,
                    "chunk_index":   idx,
                    "product_title": product.title,
                    # Store the raw text in metadata so dense_retrieve
                    # can return it without a secondary DB lookup
                    "text":          text[:1000],  # Pinecone metadata max ~40KB per vector
                },
            })

        # Batch upsert to Pinecone (max 100 vectors per request)
        if pc_index and pinecone_vectors:
            batch_size = 100
            for i in range(0, len(pinecone_vectors), batch_size):
                pc_index.upsert(vectors=pinecone_vectors[i:i + batch_size])

        logger.info(
            "RAG indexed product %s: %d created, %d updated, %d Pinecone vectors",
            product_id, created_count, updated_count, len(pinecone_vectors),
        )
        return {
            "product_id": product_id,
            "created":    created_count,
            "updated":    updated_count,
            "pinecone":   len(pinecone_vectors),
        }

    except Exception as exc:
        logger.error("RAG indexing failed for product %s: %s", product_id, exc)
        raise self.retry(exc=exc)


@shared_task(
    queue="ml",
    name="chatbot.rebuild_rag_index",
)
def rebuild_rag_index() -> dict:
    """
    Nightly full rebuild of the RAG index. Runs at 4 AM UTC via Celery Beat.

    Steps:
      1. Delete and recreate the Pinecone index (removes stale vectors)
      2. Reset RAGDocument.is_indexed flags in PostgreSQL
      3. Queue index_product_chunks for every product
    """
    from django.conf import settings
    from pinecone import Pinecone, ServerlessSpec

    from core.models import Product

    logger.info("Starting full RAG index rebuild (Pinecone)...")

    # ── Recreate Pinecone index ───────────────────────────────────────────────
    try:
        pc         = Pinecone(api_key=settings.PINECONE_API_KEY)
        index_name = getattr(settings, "PINECONE_INDEX_NAME", "sweetlatex-rag")
        dim        = int(getattr(settings, "PINECONE_DIMENSION", 384))

        existing = [idx.name for idx in pc.list_indexes()]
        if index_name in existing:
            pc.delete_index(index_name)
            logger.info("Pinecone index '%s' deleted.", index_name)

        pc.create_index(
            name=index_name,
            dimension=dim,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        logger.info("Pinecone index '%s' recreated (dim=%d).", index_name, dim)

        # Reset singleton so workers re-connect to the new index
        import ml.rag_pipeline as rag
        rag._pinecone_index = None

    except Exception as exc:
        logger.error("Pinecone index reset failed: %s", exc)

    # ── Reset DB flags and re-queue ───────────────────────────────────────────
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
            "question": [
                m.session.messages.filter(role="user")
                .order_by("-created_at")
                .values_list("content", flat=True)
                .first() or ""
                for m in messages
            ],
            "answer":   [m.content for m in messages],
            "contexts": [[c["text"] for c in m.retrieved_chunks] for m in messages],
        }

        dataset = Dataset.from_dict(data)
        result  = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision],
        )

        scores_df = result.to_pandas()

        for i, msg in enumerate(messages):
            msg.faithfulness      = float(scores_df.iloc[i].get("faithfulness", 0) or 0)
            msg.answer_relevance  = float(scores_df.iloc[i].get("answer_relevancy", 0) or 0)
            msg.context_precision = float(scores_df.iloc[i].get("context_precision", 0) or 0)

        ChatMessage.objects.bulk_update(
            messages,
            ["faithfulness", "answer_relevance", "context_precision"],
            batch_size=50,
        )

        avg_faithfulness      = scores_df["faithfulness"].mean()
        avg_answer_relevance  = scores_df["answer_relevancy"].mean()
        avg_context_precision = scores_df["context_precision"].mean()

        logger.info(
            "RAGAS evaluation complete: faithfulness=%.3f, "
            "answer_relevance=%.3f, context_precision=%.3f",
            avg_faithfulness, avg_answer_relevance, avg_context_precision,
        )

        return {
            "evaluated":         len(messages),
            "faithfulness":       round(avg_faithfulness, 4),
            "answer_relevance":   round(avg_answer_relevance, 4),
            "context_precision":  round(avg_context_precision, 4),
        }

    except Exception as exc:
        logger.error("RAGAS evaluation failed: %s", exc)
        return {"error": str(exc)}