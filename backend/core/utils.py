# core/utils.py
from django.db import transaction

from core.models import Cart, CartItem


def merge_carts(user, session_id):
    with transaction.atomic():
        try:
            guest_cart = Cart.objects.get(session_id=session_id)
            user_cart, _ = Cart.objects.get_or_create(user=user)

            guest_items = CartItem.objects.filter(cart=guest_cart)
            for item in guest_items:
                # Update or create the item in the user's cart
                user_item, created = CartItem.objects.get_or_create(
                    cart=user_cart,
                    product=item.product,
                    size=item.size,
                    defaults={"quantity": item.quantity},
                )
                if not created:
                    user_item.quantity += item.quantity
                    user_item.save()

            # Wipe the guest cart after successful migration
            guest_cart.delete()
        except Cart.DoesNotExist:
            pass
