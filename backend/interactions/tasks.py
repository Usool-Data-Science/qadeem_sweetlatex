"""
interactions/tasks.py

Celery tasks that keep derived tables up to date:
  - update_product_popularity  — called on every interaction (debounced)
  - recompute_all_popularity   — nightly Celery Beat job, full recalculation
"""

import logging
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
