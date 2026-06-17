"""
recommendations/signals.py

Triggers CLIP embedding generation whenever a new ProductImage is saved.
This keeps the FAISS index up to date without any manual intervention.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="core.ProductImage")
def trigger_clip_embedding_on_image_save(sender, instance, created, **kwargs):
    """
    When a ProductImage is saved with an image_url (i.e. after Cloudinary upload),
    dispatch the CLIP embedding Celery task.

    We check image_url rather than `created` because Cloudinary upload happens
    in a separate Celery task that updates image_url after the initial save.
    """
    if not instance.image_url:
        return

    from recommendations.tasks import generate_clip_embedding

    generate_clip_embedding.delay(
        product_id=str(instance.product_id),
        image_url=instance.image_url,
    )
    logger.debug(
        "Queued CLIP embedding for product %s (image: %s)",
        instance.product_id,
        instance.image_url,
    )


@receiver(post_save, sender="core.Product")
def trigger_sbert_embedding_on_product_save(sender, instance, **kwargs):
    """
    Generate SBERT text embedding whenever product title/style/composition changes.
    """
    from recommendations.tasks import generate_sbert_embedding

    generate_sbert_embedding.delay(product_id=str(instance.product_id))
