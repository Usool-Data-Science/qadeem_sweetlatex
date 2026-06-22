from uuid import UUID

import cloudinary.uploader
from celery import shared_task
from core.models import ArtistImage, Order, ProductImage, ProductSize
from django.conf import settings
from django.core.mail import BadHeaderError, send_mail
from django.db import transaction
from django.db.models import F
from django.template import loader
from django.utils.html import strip_tags


@shared_task
def celery_test():
    print("CELERY IS WORKING!!!")


@shared_task
def upload_image_to_cloudinary(target_obj, image_id):
    """
    Now that STORAGES["default"] = CloudinaryStorage, Django saves the image
    directly to Cloudinary when the ImageField is saved. The image_url and
    public_id are therefore already available on the model instance.

    This task now just reads those values back from Cloudinary storage and
    updates image_url / public_id on the row — without re-uploading anything.
    """
    if isinstance(image_id, str):
        try:
            image_id = UUID(image_id)
        except ValueError:
            pass

    OBJECTS = {"artist": ArtistImage, "product": ProductImage}
    print(f"CELERY: Syncing image metadata for {image_id}")

    try:
        image_obj = OBJECTS[target_obj].objects.get(id=image_id)

        if not image_obj.image:
            print("No image file found")
            return

        # CloudinaryStorage saves to Cloudinary on .save() — the image field
        # name IS the Cloudinary public_id. We build the secure URL from it.
        # image.name is the Cloudinary public_id (e.g. "products/abc123.jpg")
        public_id = image_obj.image.name

        # Build the secure Cloudinary URL
        from cloudinary.utils import cloudinary_url

        secure_url, _ = cloudinary_url(public_id, secure=True)

        image_obj.image_url = secure_url
        image_obj.public_id = public_id
        image_obj.save(update_fields=["image_url", "public_id"])

        print(f"Image metadata synced for {image_id}: {secure_url}")

    except Exception as e:
        print("CELERY ERROR:", str(e))


@shared_task
def delete_image_from_cloudinary(public_id):
    if public_id:
        cloudinary.uploader.destroy(public_id)


@shared_task
def contact_us_task(email, subject=None, body=None):
    print("subject: ", subject)
    if not subject:
        subject = "Potential customer"
    if not body:
        body = "Please consider responding with relevant information about your available products or services."
    ctx = {"subject": subject, "sender_email": email, "body": body}
    html_msg = loader.render_to_string("contact/contact-us.html", context=ctx)
    txt_msg = strip_tags(html_msg)

    try:
        send_mail(
            subject,
            txt_msg,
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
            html_message=html_msg,
        )
    except BadHeaderError:
        pass

    return "Contact us message sent"


@shared_task
def send_order_confirmation_email(email, order_id):
    subject = f"Order Confirmation - {order_id}"
    ctx = {"subject": subject, "order_id": order_id}
    html_msg = loader.render_to_string("orders/order_confirmation.html", context=ctx)
    txt_msg = strip_tags(html_msg)

    try:
        send_mail(
            subject,
            txt_msg,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
            html_message=html_msg,
        )
    except BadHeaderError:
        pass

    return f"Order confirmation email sent to {email}"


@shared_task
def release_unpaid_order_stock(order_id):
    """
    If the order is still Pending after X minutes, cancel it
    and return the stock to the ProductSize pool.
    """
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(
                order_id=order_id, status=Order.OrderStatus.PENDING
            )

            for item in order.items.all():
                ProductSize.objects.filter(id=item.size.id).update(
                    stock=F("stock") + item.quantity
                )

            order.status = Order.OrderStatus.CANCELLED
            order.save()
            print(f"Stock released for expired Order {order_id}")

    except Order.DoesNotExist:
        pass
