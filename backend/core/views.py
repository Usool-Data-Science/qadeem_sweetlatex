import json

import stripe
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
)
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from sweetlatexBE.permissions import AdminApiAuthMixin
from tasks.tasks import contact_us_task, release_unpaid_order_stock

from .models import (
    Artist,
    ArtistImage,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Product,
    ProductImage,
    ProductSize,
)
from .serializers import (
    ArtistSerializer,
    CartSerializer,
    OrderSerializer,
    ProductSerializer,
)

stripe.api_key = settings.STRIPE_SECRET_KEY


class ContactView(APIView):
    authentication_classes = ()
    permission_classes = [AllowAny]
    throttle_scope = "contact"

    def post(self, request):
        email = request.data.get("email")
        subject = request.data.get("subject")
        body = request.data.get("body")
        if not email or not subject or not body:
            return Response(
                {"error": "Email, subject, and body are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        contact_us_task.delay(email, subject=subject, body=body)
        return Response(
            {"message": "Contact request received"}, status=status.HTTP_202_ACCEPTED
        )


class ProductListView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(cache_page(60 * 60 * 2, key_prefix="product_list_cache"))
    def get(self, request):
        # 1. Get limit and offset from the URL (e.g., /products/?limit=10&offset=0)
        # Default to None if not provided to keep it backward compatible
        limit = request.query_params.get("limit")
        offset = request.query_params.get("offset")

        # Optimization: prefetch images and sizes
        products = Product.objects.prefetch_related("images", "sizes").all()

        # 2. Get total count BEFORE slicing (needed for frontend pagination math)
        total_count = products.count()

        # 3. Apply slicing if limit and offset are provided
        if limit is not None and offset is not None:
            try:
                limit = int(limit)
                offset = int(offset)
                products = products[offset : offset + limit]
            except ValueError:
                pass  # Or handle error for invalid integers

        serializer = ProductSerializer(products, many=True)

        # 4. Return both the data AND the total count
        return Response({"products": serializer.data, "total": total_count})


class SingleProductView(AdminApiAuthMixin, APIView):
    parser_classes = [MultiPartParser, FormParser]
    throttle_scope = "product"

    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def get(self, request, id):
        product = get_object_or_404(
            Product.objects.prefetch_related("images", "sizes"), product_id=id
        )
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        data = request.data
        artist = get_object_or_404(Artist, name=data.get("artist_name"))

        # Create Product
        product = Product.objects.create(
            title=data["title"],
            artist=artist,
            goal=int(data.get("goal", 0)),
            deadline=data.get("deadline"),  # Ensure this is a datetime string
            color=data.get("color", ""),
            style=data.get("style", ""),
            composition=data.get("composition", ""),
            price=float(data.get("price", 0)),
        )

        # Create sizes - Logic handled safely
        sizes_data = data.get("sizes", [])
        if isinstance(sizes_data, str):
            sizes_data = json.loads(sizes_data)

        for s in sizes_data:
            ProductSize.objects.create(
                product=product, size=s["size"], stock=int(s.get("stock", 0))
            )

        # Create images
        for img in request.FILES.getlist("images"):
            ProductImage.objects.create(product=product, image=img)

        return Response(ProductSerializer(product).data, status=201)

    def patch(self, request, id, *args, **kwargs):
        try:
            product = Product.objects.get(product_id=id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def put(self, request, id, *args, **kwargs):
        try:
            product = Product.objects.get(product_id=id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        serializer = ProductSerializer(product, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, id=None):
        if not id:
            return Response(
                {"error": "Product Id is required!"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            product = Product.objects.get(product_id=id)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product does not exist!"}, status=status.HTTP_404_NOT_FOUND
            )
        product.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ArtistView(AdminApiAuthMixin, APIView):
    def get(self, request):
        artists = Artist.objects.prefetch_related("products")
        serializer = ArtistSerializer(artists, many=True)
        return Response(serializer.data)


class SingleArtistView(AdminApiAuthMixin, APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, id, *args, **kwargs):
        if not id:
            return Response(
                {"error": "Artist Id is required!"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            artist = Artist.objects.get(id=id)
        except Artist.DoesNotExist:
            return Response(
                {"error": "Artist does not exist"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ArtistSerializer(artist, many=False)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        image = request.FILES.get("image")

        serializer = ArtistSerializer(data=data)
        if serializer.is_valid():
            with transaction.atomic():
                artist = serializer.save()

                if image:
                    ArtistImage.objects.create(image=image, artist=artist)

            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)

    def put(self, request, id=None):
        if not id:
            return Response({"error": "Artist Id is required!"}, status=400)

        try:
            artist = Artist.objects.get(id=id)
        except Artist.DoesNotExist:
            return Response({"error": "Artist not found"}, status=404)

        serializer = ArtistSerializer(artist, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

    def patch(self, request, id=None):
        try:
            artist = Artist.objects.get(id=id)
        except Artist.DoesNotExist:
            return Response({"error": "Artist not found"}, status=404)

        serializer = ArtistSerializer(artist, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

    def delete(self, request, id=None):
        if not id:
            return Response(
                {"error": "Artist Id is required!"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            artist = Artist.objects.get(id=id)
        except Artist.DoesNotExist:
            return Response(
                {"error": "Artist does not exist!"}, status=status.HTTP_404_NOT_FOUND
            )
        artist.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CartView(APIView):
    # Remove IsAuthenticated to allow guests
    permission_classes = [AllowAny]
    throttle_scope = "cart"

    def get_cart_query(self, request):
        """Helper to find cart by user or session."""
        if request.user.is_authenticated:
            return Cart.objects.get_or_create(user=request.user)

        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            # You can also use Django's built-in session_key
            request.session.create()
            session_id = request.session.session_key

        return Cart.objects.get_or_create(session_id=session_id)

    def get(self, request, *args, **kwargs):
        cart, _ = self.get_cart_query(request)

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        cart, _ = self.get_cart_query(request)
        quantity = int(request.data.get("quantity", 1))
        size_value = request.data.get("size")
        product_id = request.data.get("product_id")

        size = get_object_or_404(
            ProductSize,
            product_id=product_id,
            size=size_value,
        )

        # Atomic update or create
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            size=size,
            product_id=product_id,
            defaults={"quantity": quantity},
        )
        if not created:
            item.quantity += quantity
        if item.quantity > size.stock:
            return Response(
                {"error": f"Only {size.stock} items left in stock."},
                status=400,
            )
        item.save()

        return Response(CartSerializer(cart).data, status=201)

    def delete(self, request):
        """Clear the entire cart."""
        cart, _ = self.get_cart_query(request)
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemDetailView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "cart"

    def get_cart_item(self, request, item_id):
        """Find cart item for either authenticated user or guest session."""
        if request.user.is_authenticated:
            return get_object_or_404(CartItem, id=item_id, cart__user=request.user)

        session_id = request.headers.get("X-Session-ID")
        return get_object_or_404(CartItem, id=item_id, cart__session_id=session_id)

    def patch(self, request, item_id):
        action = request.data.get("action")
        item = self.get_cart_item(request, item_id)

        if action == "incr":
            item.quantity += 1
        elif action == "decr":
            item.quantity = max(1, item.quantity - 1)

        item.save()
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, item_id):
        item = self.get_cart_item(request, item_id)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        # Use select_related to get the cart and user in one go
        cart = get_object_or_404(Cart, user=user)

        if not cart.items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        line_items = []
        cart_items = cart.items.select_related("product", "size")
        items_to_create = []

        # 1. Initial Stock Check (Quick fail before we start creating objects)
        for item in cart_items:
            if item.size.stock < item.quantity:
                return Response(
                    {
                        "error": f"Insufficient stock for {item.product.title} ({item.size.size})"
                    },
                    status=400,
                )
            items_to_create.append(item)

            line_items.append(
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"{item.product.title} - {item.size.size}"
                        },
                        "unit_amount": int(item.product.price * 100),
                    },
                    "quantity": item.quantity,
                }
            )

        # 2. Create the Order Record
        order = Order.objects.create(user=user, status=Order.OrderStatus.PENDING)

        # 3. Reserve Stock and Create OrderItems
        for item in items_to_create:
            # The "updated" check ensures concurrency safety
            updated = ProductSize.objects.filter(
                id=item.size.id, stock__gte=item.quantity
            ).update(stock=F("stock") - item.quantity)

            if not updated:
                # Trigger rollback if stock was snatched by someone else in the last millisecond
                raise Exception(
                    f"Stock changed for {item.product.title} during checkout."
                )

            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                size=item.size,
                price_at_purchase=item.product.price,
            )

        # 4. Schedule the "Stock Release" Task (30-minute window to pay)
        # We pass the order_id as a string because UUIDs aren't always JSON serializable for Celery
        release_unpaid_order_stock.apply_async((str(order.order_id),), countdown=1800)

        # 5. Create Stripe Session
        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email=user.email,
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                success_url=settings.STRIPE_SUCCESS_URL,
                cancel_url=settings.STRIPE_CANCEL_URL,
                metadata={"order_id": str(order.order_id)},
            )
            return Response({"session_url": checkout_session.url})
        except Exception as e:
            # Transaction atomic rolls back the Order and the Stock deductions
            return Response({"error": str(e)}, status=500)


class OrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        orders = Order.objects.filter(user=request.user)

        response = OrderSerializer(orders, many=True).data
        return Response(response)


class SingleOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        order = get_object_or_404(Order, order_id=id, user=request.user)
        return Response(OrderSerializer(order).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get("Stripe-Signature")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return Response(status=400)

    if event["type"] == "checkout.session.completed":
        session = stripe.checkout.Session.retrieve(
            event["data"]["object"].id, expand=["line_items", "customer"]
        )
        order_id = session["metadata"]["order_id"]

        if order_id:
            with transaction.atomic():
                try:
                    # select_for_update locks the row so Celery and Webhook don't collide
                    order = Order.objects.select_for_update().get(order_id=order_id)

                    if order.status == Order.OrderStatus.PENDING:
                        order.status = Order.OrderStatus.COMPLETED
                        order.save()

                        # Clear ONLY the items, keep the Cart object itself
                        CartItem.objects.filter(cart__user=order.user).delete()

                        # Trigger email
                        # send_order_confirmation.delay(str(order.order_id))
                except Order.DoesNotExist:
                    return Response({"error": "Order not found"}, status=404)

    return Response(status=200)
