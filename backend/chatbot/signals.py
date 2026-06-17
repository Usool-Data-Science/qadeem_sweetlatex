"""
chatbot/signals.py

Auto-triggers RAG chunk generation whenever a Product is saved.
Keeps the knowledge base current without manual intervention.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="core.Product")
def index_product_in_rag(sender, instance, created, **kwargs):
    """
    Queue a RAG indexing task whenever a product is created or updated.
    Runs asynchronously so the save() call is never blocked.
    """
    from chatbot.tasks import index_product_chunks
    index_product_chunks.delay(str(instance.product_id))
    logger.debug("Queued RAG indexing for product %s", instance.product_id)
