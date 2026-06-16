from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from tasks.tasks import delete_image_from_cloudinary, upload_image_to_cloudinary

from .models import ArtistImage, Product, ProductImage


### ARTIST SIGNALS
@receiver(post_save, sender=ArtistImage)
def handle_upload_artist_image(sender, instance, created, **kwargs):
    # 1. If the instance is created, or update and instance has image:
    if created or getattr(instance, "_image_changed", False) and instance.image:
        print("SIGNAL -> scheduling upload AFTER COMMIT")
        print(f"SIGNAL: Processing image {instance.id}")
        transaction.on_commit(
            lambda: upload_image_to_cloudinary.delay("artist", instance.id)
        )


@receiver(pre_save, sender=ArtistImage)
def handle_delete_previous_artist_image(sender, instance, **kwargs):
    if not instance.id:
        # New artist no need to change image
        return
    try:
        old = ArtistImage.objects.get(id=instance.id)
    except ArtistImage.DoesNotExist:
        return

    if old.image != instance.image:
        instance._image_changed = True

        if old.public_id:
            delete_image_from_cloudinary.delay(old.public_id)


@receiver(post_delete, sender=ArtistImage)
def handle_delete_image(sender, instance, **kwargs):
    if instance.public_id:
        delete_image_from_cloudinary.delay(instance.public_id)


### PRODUCT SIGNALS
@receiver(pre_save, sender=ProductImage)
def handle_delete_previous_image(sender, instance, **kwargs):
    if not instance.id:
        return

    try:
        old = ProductImage.objects.get(id=instance.id)
    except ProductImage.DoesNotExist:
        return

    if old.image != instance.image:
        instance._image_changed = True

        if old.public_id:
            delete_image_from_cloudinary.delay(old.public_id)


@receiver(post_save, sender=ProductImage)
def handle_new_image_upload(sender, instance, created, **kwargs):
    """Checks if image exist (new or updated) then upload them to cloudinary"""
    if (created or getattr(instance, "_image_changed", False)) and instance.image:
        print("SIGNAL -> scheduling upload AFTER COMMIT")
        transaction.on_commit(
            lambda: upload_image_to_cloudinary.delay("product", instance.id)
        )


@receiver(post_delete, sender=ProductImage)
def handle_delete_image(sender, instance, **kwargs):
    if instance.public_id:
        delete_image_from_cloudinary.delay(instance.public_id)


@receiver([post_delete, post_save], sender=Product)
def invalidate_product_key(sender, instance, **kwargs):
    print("Clearing product cache ...")
    cache.delete_pattern("*product_*")
