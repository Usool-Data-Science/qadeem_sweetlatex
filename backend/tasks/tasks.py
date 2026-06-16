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
    if isinstance(image_id, str):
        try:
            image_id = UUID(image_id)
        except ValueError:
            pass
    OBJECTS = {"artist": ArtistImage, "product": ProductImage}
    print(f"CELERY: Processing image {image_id}")

    try:
        image_obj = OBJECTS[target_obj].objects.get(id=image_id)

        if not image_obj.image:
            print("No image file found")
            return

        upload_result = cloudinary.uploader.upload(image_obj.image.path)

        image_obj.image_url = upload_result["secure_url"]
        image_obj.public_id = upload_result["public_id"]

        # delete local file AFTER upload
        image_obj.image.delete(save=False)

        image_obj.save()

        print(f"Upload of image-{image_id} complete")
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
            [
                settings.DEFAULT_FROM_EMAIL,
            ],
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
            [
                email,
            ],
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
            # Select for update to prevent race conditions during the release
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
        # Order was either already completed or doesn't exist
        pass
