"""
interactions/signals.py

Django signals that auto-create UserInteraction rows whenever core events fire.
This keeps the interactions app decoupled — core.models never imports us.

Signals wired:
  - Order COMPLETED  → PURCHASE interaction for each OrderItem
  - CartItem created → CART_ADD interaction
  - CartItem deleted → CART_REMOVE interaction
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from interactions.models import INTERACTION_WEIGHTS, InteractionType, UserInteraction


@receiver(post_save, sender="core.Order")
def log_purchase_on_order_complete(sender, instance, **kwargs):
    """
    When an order transitions to COMPLETED, log a PURCHASE interaction for
    every product in the order.  We only fire on status change to avoid
    duplicate rows on unrelated saves.
    """
    from core.models import Order

    if instance.status != Order.OrderStatus.COMPLETED:
        return

    # Guard: only process if this is a status-change save (not creation)
    # We check the DB value to detect the transition
    try:
        previous = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    weight = INTERACTION_WEIGHTS[InteractionType.PURCHASE]
    interactions = [
        UserInteraction(
            user=instance.user,
            product=item.product,
            interaction_type=InteractionType.PURCHASE,
            weight=weight,
            metadata={"order_id": str(instance.order_id), "quantity": item.quantity},
        )
        for item in instance.items.select_related("product").all()
    ]
    UserInteraction.objects.bulk_create(interactions, ignore_conflicts=True)


@receiver(post_save, sender="core.CartItem")
def log_cart_add(sender, instance, created, **kwargs):
    if not created:
        return
    UserInteraction.objects.create(
        user=instance.cart.user,
        session_key=instance.cart.session_id,
        product=instance.product,
        interaction_type=InteractionType.CART_ADD,
        weight=INTERACTION_WEIGHTS[InteractionType.CART_ADD],
        metadata={"quantity": instance.quantity, "size": str(instance.size)},
    )


@receiver(post_delete, sender="core.CartItem")
def log_cart_remove(sender, instance, **kwargs):
    UserInteraction.objects.create(
        user=instance.cart.user,
        session_key=instance.cart.session_id,
        product=instance.product,
        interaction_type=InteractionType.CART_REMOVE,
        weight=INTERACTION_WEIGHTS[InteractionType.CART_REMOVE],
        metadata={"quantity": instance.quantity},
    )
