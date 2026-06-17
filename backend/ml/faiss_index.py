"""
ml/faiss_index.py

FAISS index manager for approximate nearest-neighbour (ANN) product search.

Architecture:
  - IndexFlatIP  (inner product = cosine on L2-normalised vectors) for accuracy
  - Upgraded to IndexIVFFlat when product count > 10,000 for speed
  - Index is persisted to disk and memory-mapped at startup
  - product_ids list is stored alongside the index to map FAISS row → product UUID

Thread safety: FAISS read operations are thread-safe. We use a module-level
lock only during index writes (rebuild).
"""

import logging
import pickle
import threading
from pathlib import Path
from typing import Optional

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

_index = None
_product_ids: list[str] = []
_lock = threading.Lock()

FAISS_INDEX_PATH = Path(getattr(settings, "FAISS_INDEX_PATH", "/app/faiss_index"))
INDEX_FILE = FAISS_INDEX_PATH / "products.index"
IDS_FILE = FAISS_INDEX_PATH / "product_ids.pkl"

# Switch to IVF when we have more products than this
IVF_THRESHOLD = 10_000


def _get_faiss():
    try:
        import faiss

        return faiss
    except ImportError as e:
        raise ImportError(
            "faiss-cpu not installed. Add 'faiss-cpu' to requirements.txt"
        ) from e


def load_index() -> bool:
    """
    Load a previously built index from disk into memory.
    Called at Django startup via AppConfig.ready() or lazily on first request.
    Returns True if loaded successfully.
    """
    global _index, _product_ids
    faiss = _get_faiss()

    if not INDEX_FILE.exists() or not IDS_FILE.exists():
        logger.warning(
            "FAISS index not found at %s — run build_faiss_index task.",
            FAISS_INDEX_PATH,
        )
        return False

    with _lock:
        _index = faiss.read_index(str(INDEX_FILE))
        with open(IDS_FILE, "rb") as f:
            _product_ids = pickle.load(f)

    logger.info("FAISS index loaded: %d products, dim=%d", len(_product_ids), _index.d)
    return True


def build_index(embedding_source: str = "clip_image") -> dict:
    """
    Build (or rebuild) the FAISS index from ProductEmbedding rows in the DB.

    Called by the nightly Celery task `rebuild_faiss_index`.
    Swaps in the new index atomically so live requests are never blocked.

    Returns metrics dict for logging to MLModelRegistry.
    """
    global _index, _product_ids
    faiss = _get_faiss()

    from recommendations.models import ProductEmbedding

    rows = list(
        ProductEmbedding.objects.filter(source=embedding_source)
        .values("product_id", "vector", "vector_dim")
        .order_by("product_id")
    )

    if not rows:
        logger.error(
            "No embeddings found for source=%s — aborting index build.",
            embedding_source,
        )
        return {"error": "no_embeddings", "count": 0}

    dim = rows[0]["vector_dim"]
    vectors = np.array([r["vector"] for r in rows], dtype=np.float32)

    # L2-normalise so inner product == cosine similarity
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    vectors = vectors / norms

    n = len(vectors)
    if n < IVF_THRESHOLD:
        new_index = faiss.IndexFlatIP(dim)
    else:
        # IVF for speed — 4*sqrt(n) centroids is a common heuristic
        n_centroids = int(4 * (n**0.5))
        quantiser = faiss.IndexFlatIP(dim)
        new_index = faiss.IndexIVFFlat(
            quantiser, dim, n_centroids, faiss.METRIC_INNER_PRODUCT
        )
        new_index.train(vectors)
        new_index.nprobe = 32  # search 32 cells per query (accuracy/speed tradeoff)

    new_index.add(vectors)
    new_product_ids = [str(r["product_id"]) for r in rows]

    # Persist to disk
    FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)
    faiss.write_index(new_index, str(INDEX_FILE))
    with open(IDS_FILE, "wb") as f:
        pickle.dump(new_product_ids, f)

    # Atomic swap — live queries during rebuild see old index, not a half-built one
    with _lock:
        _index = new_index
        _product_ids = new_product_ids

    logger.info(
        "FAISS index rebuilt: %d products, dim=%d, type=%s",
        n,
        dim,
        type(new_index).__name__,
    )
    return {"count": n, "dim": dim, "type": type(new_index).__name__}


def search(
    query_vector: list[float],
    top_k: int = 20,
    exclude_ids: Optional[set[str]] = None,
) -> list[tuple[str, float]]:
    """
    Search the FAISS index for the top_k most similar products.

    Args:
        query_vector:  L2-normalised embedding vector (list of floats)
        top_k:         number of results to return
        exclude_ids:   set of product UUID strings to skip (e.g. already viewed)

    Returns:
        List of (product_uuid_str, score) tuples, sorted by score descending.
    """
    global _index, _product_ids

    if _index is None:
        loaded = load_index()
        if not loaded:
            logger.warning("FAISS index unavailable — returning empty results.")
            return []

    exclude_ids = exclude_ids or set()
    query = np.array([query_vector], dtype=np.float32)

    # Fetch more than top_k to account for exclusions
    fetch_k = min(top_k + len(exclude_ids) + 10, len(_product_ids))

    with _lock:
        scores, indices = _index.search(query, fetch_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(_product_ids):
            continue
        pid = _product_ids[idx]
        if pid in exclude_ids:
            continue
        results.append((pid, float(score)))
        if len(results) >= top_k:
            break

    return results
