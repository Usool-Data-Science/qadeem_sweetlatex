"""
recommendations/tasks.py

Celery tasks for the recommendations pipeline:

  generate_clip_embedding   — triggered by ProductImage post_save signal
  generate_sbert_embedding  — triggered by Product post_save signal
  rebuild_faiss_index       — nightly Celery Beat job
  train_bpr                 — nightly Celery Beat job
  train_sasrec              — nightly Celery Beat job
  refresh_user_recommendations — called after significant interaction events
"""

import logging
import time
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    queue="ml",
    name="interactions.update_product_popularity",
)
def update_product_popularity(self, product_id: str) -> None:
    """
    Recompute the popularity score for a single product.
    Called asynchronously after every logged interaction.

    Score formula:
        Σ (weight × decay_factor) over 30-day rolling window
        decay_factor = exp(-λ × days_ago),  λ = 0.05
    """
    import math

    from interactions.models import (
        InteractionType,
        ProductPopularityScore,
        UserInteraction,
    )

    try:
        from core.models import Product

        product = Product.objects.get(product_id=product_id)
    except Exception as exc:
        logger.warning(
            "Product %s not found for popularity update: %s", product_id, exc
        )
        return

    window_start = timezone.now() - timedelta(days=30)
    interactions = (
        UserInteraction.objects.filter(
            product_id=product.pk, created_at__gte=window_start
        )
        .exclude(interaction_type=InteractionType.CHAT)
        .values("interaction_type", "weight", "created_at")
    )

    lam = 0.05
    score = 0.0
    view_count = purchase_count = cart_add_count = 0

    for row in interactions:
        days_ago = (timezone.now() - row["created_at"]).total_seconds() / 86400
        decay = math.exp(-lam * days_ago)
        score += row["weight"] * decay

        if row["interaction_type"] == InteractionType.VIEW:
            view_count += 1
        elif row["interaction_type"] == InteractionType.PURCHASE:
            purchase_count += 1
        elif row["interaction_type"] == InteractionType.CART_ADD:
            cart_add_count += 1

    ProductPopularityScore.objects.update_or_create(
        product=product,
        defaults={
            "score": round(score, 4),
            "view_count": view_count,
            "purchase_count": purchase_count,
            "cart_add_count": cart_add_count,
        },
    )
    logger.debug("Popularity updated: product=%s score=%.4f", product_id, score)


@shared_task(
    queue="ml",
    name="interactions.recompute_all_popularity",
)
def recompute_all_popularity() -> dict:
    """
    Nightly Celery Beat task — full recalculation for all products.
    Scheduled in CELERY_BEAT_SCHEDULE (settings).
    """
    from core.models import Product

    product_ids = list(Product.objects.values_list("product_id", flat=True))
    logger.info("Recomputing popularity for %d products", len(product_ids))

    for pid in product_ids:
        update_product_popularity.delay(str(pid))

    return {"scheduled": len(product_ids)}


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    queue="ml",
    name="recommendations.generate_clip_embedding",
)
def generate_clip_embedding(self, product_id: str, image_url: str) -> dict:
    """
    Generate a CLIP image embedding for a product and store it in the DB.
    Triggered automatically when a ProductImage is saved with an image_url.
    """
    try:
        from ml.clip_encoder import encode_image_from_url

        from recommendations.models import EmbeddingSource, ProductEmbedding

        vector = encode_image_from_url(image_url)
        if vector is None:
            raise ValueError(f"CLIP encoding returned None for {image_url}")

        from core.models import Product

        product = Product.objects.get(product_id=product_id)

        obj, created = ProductEmbedding.objects.update_or_create(
            product=product,
            source=EmbeddingSource.CLIP_IMAGE,
            defaults={
                "vector": vector,
                "vector_dim": len(vector),
                "model_version": "clip-vit-b32-v1",
            },
        )
        action = "created" if created else "updated"
        logger.info(
            "CLIP embedding %s for product %s (dim=%d)", action, product_id, len(vector)
        )
        return {"product_id": product_id, "dim": len(vector), "action": action}

    except Exception as exc:
        logger.error("CLIP embedding failed for %s: %s", product_id, exc)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    queue="ml",
    name="recommendations.generate_sbert_embedding",
)
def generate_sbert_embedding(self, product_id: str) -> dict:
    """
    Generate a Sentence-BERT text embedding from product title + style + composition.
    """
    try:
        from core.models import Product
        from sentence_transformers import SentenceTransformer

        from recommendations.models import EmbeddingSource, ProductEmbedding

        product = Product.objects.get(product_id=product_id)
        text = f"{product.title}. Style: {product.style}. Color: {product.color}. {product.composition}"

        model = SentenceTransformer("all-MiniLM-L6-v2")
        vector = model.encode(text, normalize_embeddings=True).tolist()

        obj, created = ProductEmbedding.objects.update_or_create(
            product=product,
            source=EmbeddingSource.SBERT_TEXT,
            defaults={
                "vector": vector,
                "vector_dim": len(vector),
                "model_version": "sbert-all-minilm-l6-v2-v1",
            },
        )
        action = "created" if created else "updated"
        logger.info(
            "SBERT embedding %s for product %s (dim=%d)",
            action,
            product_id,
            len(vector),
        )
        return {"product_id": product_id, "dim": len(vector), "action": action}

    except Exception as exc:
        logger.error("SBERT embedding failed for %s: %s", product_id, exc)
        raise self.retry(exc=exc)


@shared_task(
    queue="ml",
    name="recommendations.rebuild_faiss_index",
)
def rebuild_faiss_index() -> dict:
    """
    Rebuild the FAISS ANN index from all current CLIP embeddings.
    Runs nightly at 3 AM UTC via Celery Beat.
    """
    logger.info("Starting FAISS index rebuild...")
    start = time.time()

    from ml import faiss_index

    from recommendations.models import MLModelRegistry

    metrics = faiss_index.build_index(embedding_source="clip_image")
    duration = int(time.time() - start)
    metrics["duration_seconds"] = duration

    # Deactivate previous FAISS entries and register new one
    MLModelRegistry.objects.filter(model_type="clip", is_active=True).update(
        is_active=False
    )
    MLModelRegistry.objects.create(
        model_type="clip",
        version=f"faiss-{timezone.now().strftime('%Y%m%d')}",
        artifact_path=str(faiss_index.INDEX_FILE),
        is_active=True,
        metrics=metrics,
        trained_on_rows=metrics.get("count", 0),
        training_duration_seconds=duration,
    )

    logger.info("FAISS rebuild complete: %s", metrics)
    return metrics


@shared_task(
    queue="ml",
    name="recommendations.train_bpr",
)
def train_bpr() -> dict:
    """
    Train BPR collaborative filtering model.
    Runs nightly at 3:30 AM UTC via Celery Beat.
    """
    logger.info("Starting BPR training...")
    from ml.bpr import BPRTrainer

    from recommendations.models import MLModelRegistry

    trainer = BPRTrainer()
    metrics = trainer.train()

    if not metrics.get("skipped"):
        MLModelRegistry.objects.filter(model_type="bpr", is_active=True).update(
            is_active=False
        )
        MLModelRegistry.objects.create(
            model_type="bpr",
            version=f"bpr-{timezone.now().strftime('%Y%m%d')}",
            artifact_path=str(BPRTrainer.__module__),
            is_active=True,
            metrics=metrics,
            trained_on_rows=metrics.get("n_interactions", 0),
            training_duration_seconds=metrics.get("duration_seconds", 0),
        )

    return metrics


@shared_task(
    queue="ml",
    name="recommendations.train_sasrec",
)
def train_sasrec() -> dict:
    """
    Train SASRec sequential recommendation model.
    Runs nightly at 4 AM UTC via Celery Beat.
    """
    logger.info("Starting SASRec training...")
    from ml.sasrec import SASREC_MODEL_PATH, SASRecTrainer

    from recommendations.models import MLModelRegistry

    trainer = SASRecTrainer()
    metrics = trainer.train()

    if not metrics.get("skipped"):
        MLModelRegistry.objects.filter(model_type="sasrec", is_active=True).update(
            is_active=False
        )
        MLModelRegistry.objects.create(
            model_type="sasrec",
            version=f"sasrec-{timezone.now().strftime('%Y%m%d')}",
            artifact_path=str(SASREC_MODEL_PATH),
            is_active=True,
            metrics=metrics,
            trained_on_rows=metrics.get("n_users", 0),
            training_duration_seconds=metrics.get("duration_seconds", 0),
        )

    return metrics


@shared_task(
    queue="ml",
    name="recommendations.refresh_user_recommendations",
    max_retries=2,
)
def refresh_user_recommendations(user_pk: str) -> dict:
    """
    Recompute and cache recommendation results for a specific user.
    Triggered after high-signal interactions (purchase, cart_add).
    Stores result in RecommendationResult with a 6-hour TTL.
    """
    from datetime import timedelta

    from ml.fusion import recommend_for_user

    from recommendations.models import RecommendationResult

    results, strategy = recommend_for_user(user_pk=user_pk, top_k=20)
    product_ids = [pid for pid, _ in results]
    scores = [score for _, score in results]

    expires_at = timezone.now() + timedelta(hours=6)

    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        return {"error": "user_not_found"}

    RecommendationResult.objects.update_or_create(
        user=user,
        anchor_product=None,
        strategy=strategy,
        defaults={
            "product_ids": product_ids,
            "scores": scores,
            "expires_at": expires_at,
        },
    )

    logger.info(
        "Refreshed recommendations for user %s (%s): %d items",
        user_pk,
        strategy,
        len(product_ids),
    )
    return {"user": user_pk, "strategy": strategy, "count": len(product_ids)}
