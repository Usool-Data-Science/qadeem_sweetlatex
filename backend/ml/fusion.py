"""
ml/fusion.py

Hybrid Recommendation Fusion Engine.

Combines scores from three sources:
  1. BPR collaborative filtering  (α)
  2. SASRec sequential model      (β)
  3. CLIP visual similarity        (γ)

Weights α, β, γ sum to 1.0 and are tunable via Django settings or
set to their defaults.  For distinction-level evaluation, run a grid search
on the validation set and store the best weights in settings.

For cold-start users (< MIN_INTERACTIONS interactions), the engine falls
back gracefully:
  - 0 interactions   → TRENDING (popularity score)
  - 1–4 interactions → CLIP similarity only (content-based)
  - 5+ interactions  → full hybrid
"""

import logging
from typing import Optional

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)

# Default fusion weights — overridable in Django settings
DEFAULT_ALPHA = float(getattr(settings, "FUSION_ALPHA", 0.35))  # BPR
DEFAULT_BETA = float(getattr(settings, "FUSION_BETA", 0.40))  # SASRec
DEFAULT_GAMMA = float(getattr(settings, "FUSION_GAMMA", 0.25))  # CLIP

MIN_INTERACTIONS = 5
TRENDING_LIMIT = 50


def _min_max_normalise(scores: dict[str, float]) -> dict[str, float]:
    """Normalise a score dict to [0, 1] range."""
    if not scores:
        return {}
    vals = np.array(list(scores.values()), dtype=np.float32)
    mn, mx = vals.min(), vals.max()
    if mx == mn:
        return {k: 1.0 for k in scores}
    return {k: float((v - mn) / (mx - mn)) for k, v in scores.items()}


def _get_trending_ids(limit: int = TRENDING_LIMIT) -> list[tuple[str, float]]:
    """Return top-popularity products as (product_uuid, score) list."""
    from interactions.models import ProductPopularityScore

    rows = (
        ProductPopularityScore.objects.select_related("product")
        .filter(product__sizes__stock__gt=0)
        .order_by("-score")
        .distinct()[:limit]
    )
    return [(str(r.product.product_id), r.score) for r in rows]


def _get_user_interaction_count(user_pk) -> int:
    from interactions.models import UserInteraction

    return UserInteraction.objects.filter(user_id=user_pk).count()


def _get_user_interacted_ids(user_pk) -> set[str]:
    """Products the user already interacted with — excluded from recommendations."""
    from interactions.models import UserInteraction

    return set(
        str(p)
        for p in UserInteraction.objects.filter(user_id=user_pk, product__isnull=False)
        .values_list("product_id", flat=True)
        .distinct()
    )


def recommend_for_user(
    user_pk: Optional[str],
    top_k: int = 12,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    gamma: float = DEFAULT_GAMMA,
) -> tuple[list[tuple[str, float]], str]:
    """
    Main entry point for the /api/recommendations/for-you/ endpoint.

    Returns:
        (ranked_results, strategy_used)
        ranked_results: list of (product_uuid, fusion_score) sorted best-first
        strategy_used:  one of RecommendationStrategy values (for logging)
    """
    from recommendations.models import RecommendationStrategy

    # ── Anonymous / no user → trending ────────────────────────────────────────
    if user_pk is None:
        return _get_trending_ids(top_k), RecommendationStrategy.TRENDING

    interaction_count = _get_user_interaction_count(user_pk)
    already_seen = _get_user_interacted_ids(user_pk)

    # ── Cold start → popularity ────────────────────────────────────────────────
    if interaction_count == 0:
        results = [
            (pid, s)
            for pid, s in _get_trending_ids(top_k + 20)
            if pid not in already_seen
        ]
        return results[:top_k], RecommendationStrategy.COLD_START

    # ── Warm-ish → content-based CLIP only ────────────────────────────────────
    if interaction_count < MIN_INTERACTIONS:
        return _content_based_for_user(
            user_pk, top_k, already_seen
        ), RecommendationStrategy.SIMILAR_ITEMS

    # ── Full hybrid ────────────────────────────────────────────────────────────
    return _hybrid_recommend(
        user_pk, top_k, alpha, beta, gamma, already_seen
    ), RecommendationStrategy.HYBRID


def _content_based_for_user(
    user_pk: str,
    top_k: int,
    already_seen: set[str],
) -> list[tuple[str, float]]:
    """
    Average the CLIP embeddings of the user's most recently viewed products
    and find nearest neighbours in FAISS.
    """
    from interactions.models import InteractionType, UserInteraction
    from ml import faiss_index
    from recommendations.models import ProductEmbedding

    recent_pids = list(
        UserInteraction.objects.filter(
            user_id=user_pk,
            product__isnull=False,
            interaction_type__in=[
                InteractionType.VIEW,
                InteractionType.CLICK,
                InteractionType.CART_ADD,
                InteractionType.PURCHASE,
            ],
        )
        .order_by("-created_at")
        .values_list("product_id", flat=True)[:10]
    )

    if not recent_pids:
        return _get_trending_ids(top_k)

    embeddings = list(
        ProductEmbedding.objects.filter(
            product_id__in=recent_pids, source="clip_image"
        ).values_list("vector", flat=True)
    )

    if not embeddings:
        return _get_trending_ids(top_k)

    avg_vector = np.mean([np.array(e) for e in embeddings], axis=0).tolist()
    return faiss_index.search(avg_vector, top_k=top_k, exclude_ids=already_seen)


def _hybrid_recommend(
    user_pk: str,
    top_k: int,
    alpha: float,
    beta: float,
    gamma: float,
    already_seen: set[str],
) -> list[tuple[str, float]]:
    """
    Fuse BPR + SASRec + CLIP scores with min-max normalisation.
    Gracefully degrades if any component is unavailable (model not trained yet).
    """
    # Fetch candidate pool from FAISS (broadest net)
    # Use the user's top-interacted product as the visual anchor
    from interactions.models import InteractionType, UserInteraction
    from ml import faiss_index
    from ml.bpr import BPRTrainer
    from ml.sasrec import SASRecTrainer
    from recommendations.models import ProductEmbedding

    anchor_row = (
        UserInteraction.objects.filter(
            user_id=user_pk,
            product__isnull=False,
            interaction_type=InteractionType.PURCHASE,
        )
        .order_by("-created_at")
        .values("product_id")
        .first()
    )

    clip_scores: dict[str, float] = {}
    if anchor_row:
        emb = (
            ProductEmbedding.objects.filter(
                product_id=anchor_row["product_id"], source="clip_image"
            )
            .values_list("vector", flat=True)
            .first()
        )

        if emb:
            faiss_results = faiss_index.search(
                emb, top_k=top_k * 4, exclude_ids=already_seen
            )
            clip_scores = {pid: score for pid, score in faiss_results}

    # Candidate product IDs = FAISS results ∪ trending (ensures non-empty pool)
    trending_ids = [pid for pid, _ in _get_trending_ids(TRENDING_LIMIT)]
    candidate_ids = list(set(clip_scores.keys()) | set(trending_ids) - already_seen)

    # BPR scores
    bpr_scores: dict[str, float] = {}
    try:
        bpr = BPRTrainer.load()
        if bpr:
            bpr_scores = bpr.score_for_user(str(user_pk), candidate_ids)
    except Exception as exc:
        logger.warning("BPR scoring failed: %s", exc)

    # SASRec scores
    sasrec_scores: dict[str, float] = {}
    try:
        sasrec = SASRecTrainer.load()
        if sasrec:
            sasrec_results = sasrec.recommend(
                str(user_pk), top_k=len(candidate_ids) * 2, exclude_ids=already_seen
            )
            sasrec_scores = dict(sasrec_results)
    except Exception as exc:
        logger.warning("SASRec scoring failed: %s", exc)

    # Normalise each component independently
    bpr_norm = _min_max_normalise(bpr_scores)
    sasrec_norm = _min_max_normalise(sasrec_scores)
    clip_norm = _min_max_normalise(clip_scores)

    # Adjust weights if components are missing
    active = sum([bool(bpr_norm), bool(sasrec_norm), bool(clip_norm)])
    if active == 0:
        return _get_trending_ids(top_k)
    if active < 3:
        # Redistribute weight evenly among available components
        w = 1.0 / active
        if not bpr_norm:
            alpha, beta, gamma = 0, w if sasrec_norm else 0, w if clip_norm else 0
        if not sasrec_norm:
            alpha, beta, gamma = w if bpr_norm else 0, 0, w if clip_norm else 0
        if not clip_norm:
            alpha, beta, gamma = w if bpr_norm else 0, w if sasrec_norm else 0, 0

    # Fuse
    fused: dict[str, float] = {}
    all_candidates = set(candidate_ids)
    for pid in all_candidates:
        if pid in already_seen:
            continue
        score = (
            alpha * bpr_norm.get(pid, 0.0)
            + beta * sasrec_norm.get(pid, 0.0)
            + gamma * clip_norm.get(pid, 0.0)
        )
        fused[pid] = score

    ranked = sorted(fused.items(), key=lambda x: -x[1])
    return ranked[:top_k]


def similar_items(
    product_id: str,
    top_k: int = 12,
) -> list[tuple[str, float]]:
    """
    Find visually similar products using FAISS nearest neighbours.
    Used by the "You might also like" carousel on the product detail page.
    """
    from ml import faiss_index
    from recommendations.models import ProductEmbedding

    emb = (
        ProductEmbedding.objects.filter(product_id=product_id, source="clip_image")
        .values_list("vector", flat=True)
        .first()
    )

    if emb is None:
        logger.warning(
            "No CLIP embedding for product %s — falling back to trending.", product_id
        )
        return _get_trending_ids(top_k)

    return faiss_index.search(emb, top_k=top_k + 1, exclude_ids={product_id})[:top_k]
