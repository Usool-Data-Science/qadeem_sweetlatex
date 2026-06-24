import json

import stripe
from django.conf import settings
from django.core.cache import cache
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

# ── Cache helpers ─────────────────────────────────────────────────────────────
PRODUCT_CACHE_PREFIX = "product_list_cache"
PRODUCT_CACHE_TTL = 60 * 60 * 2  # 2 hours
PAGE_SIZE_DEFAULT = 9
PAGE_SIZE_MAX = 50


def _invalidate_product_cache():
    """
    Delete all cached product list pages.

    Uses django-redis `delete_pattern` when available (production Redis).
    Falls back to a manual key sweep for other backends (e.g. LocMemCache in dev).
    Works by iterating the known page range and deleting each key explicitly
    so it doesn't rely on pattern matching.
    """
    try:
        # Redis backend — fast wildcard delete
        cache.delete_pattern(f"*{PRODUCT_CACHE_PREFIX}*")
    except AttributeError:
        # Non-Redis backend (e.g. LocMemCache) — delete known key patterns
        # This covers pages 1–20 with sizes 6, 9, 12 which covers all realistic usage
        for page in range(1, 21):
            for size in [6, 9, 12, PAGE_SIZE_DEFAULT]:
                cache.delete(f"{PRODUCT_CACHE_PREFIX}:page{page}:size{size}")


# ── Contact ───────────────────────────────────────────────────────────────────


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


# ── Products ──────────────────────────────────────────────────────────────────


class ProductListView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(cache_page(PRODUCT_CACHE_TTL, key_prefix=PRODUCT_CACHE_PREFIX))
    def get(self, request):
        """
        GET /api/products/?page=1&page_size=9

        Returns paginated products with total count and pagination metadata.
        The cache key includes all query params so different pages are cached
        independently. Cache is invalidated on every create/update/delete.

        Response shape:
        {
            "products":    [...],
            "total":       42,
            "page":        1,
            "page_size":   9,
            "total_pages": 5,
            "has_next":    true,
            "has_prev":    false
        }
        """
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = min(
                PAGE_SIZE_MAX,
                max(1, int(request.query_params.get("page_size", PAGE_SIZE_DEFAULT))),
            )
        except (ValueError, TypeError):
            page = 1
            page_size = PAGE_SIZE_DEFAULT

        products = Product.objects.prefetch_related("images", "sizes").all()
        total = products.count()

        offset = (page - 1) * page_size
        products = products[offset : offset + page_size]

        total_pages = max(1, (total + page_size - 1) // page_size)

        serializer = ProductSerializer(products, many=True)
        return Response(
            {
                "products": serializer.data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        )


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
        return Response(ProductSerializer(product).data)

    @transaction.atomic
    def post(self, request):
        data = request.data
        artist = get_object_or_404(Artist, name=data.get("artist_name"))

        product = Product.objects.create(
            title=data["title"],
            artist=artist,
            goal=int(data.get("goal", 0)),
            deadline=data.get("deadline"),
            color=data.get("color", ""),
            style=data.get("style", ""),
            composition=data.get("composition", ""),
            price=float(data.get("price", 0)),
        )

        sizes_data = data.get("sizes", [])
        if isinstance(sizes_data, str):
            sizes_data = json.loads(sizes_data)
        for s in sizes_data:
            ProductSize.objects.create(
                product=product, size=s["size"], stock=int(s.get("stock", 0))
            )

        for img in request.FILES.getlist("images"):
            ProductImage.objects.create(product=product, image=img)

        _invalidate_product_cache()
        return Response(ProductSerializer(product).data, status=201)

    def patch(self, request, id, *args, **kwargs):
        product = get_object_or_404(Product, product_id=id)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            _invalidate_product_cache()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def put(self, request, id, *args, **kwargs):
        product = get_object_or_404(Product, product_id=id)
        serializer = ProductSerializer(product, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            _invalidate_product_cache()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, id=None):
        if not id:
            return Response(
                {"error": "Product Id is required!"}, status=status.HTTP_400_BAD_REQUEST
            )
        product = get_object_or_404(Product, product_id=id)
        product.delete()
        _invalidate_product_cache()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Artists ───────────────────────────────────────────────────────────────────


class ArtistView(AdminApiAuthMixin, APIView):
    def get(self, request):
        artists = Artist.objects.prefetch_related("products")
        serializer = ArtistSerializer(artists, many=True)
        return Response(serializer.data)


class SingleArtistView(AdminApiAuthMixin, APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, id, *args, **kwargs):
        artist = get_object_or_404(Artist, id=id)
        serializer = ArtistSerializer(artist, many=False)
        return Response(serializer.data)

    def post(self, request):
        image = request.FILES.get("image")
        serializer = ArtistSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                artist = serializer.save()
                if image:
                    ArtistImage.objects.create(image=image, artist=artist)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def put(self, request, id=None):
        artist = get_object_or_404(Artist, id=id)
        serializer = ArtistSerializer(artist, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def patch(self, request, id=None):
        artist = get_object_or_404(Artist, id=id)
        serializer = ArtistSerializer(artist, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, id=None):
        artist = get_object_or_404(Artist, id=id)
        artist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Cart ──────────────────────────────────────────────────────────────────────


class CartView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "cart"

    def get_cart_query(self, request):
        if request.user.is_authenticated:
            return Cart.objects.get_or_create(user=request.user)
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        return Cart.objects.get_or_create(session_id=session_id)

    def get(self, request, *args, **kwargs):
        cart, _ = self.get_cart_query(request)
        return Response(CartSerializer(cart).data)

    def post(self, request):
        cart, _ = self.get_cart_query(request)
        quantity = int(request.data.get("quantity", 1))
        size_value = request.data.get("size")
        product_id = request.data.get("product_id")

        size = get_object_or_404(ProductSize, product_id=product_id, size=size_value)

        item, created = CartItem.objects.get_or_create(
            cart=cart, size=size, product_id=product_id, defaults={"quantity": quantity}
        )
        if not created:
            item.quantity += quantity
        if item.quantity > size.stock:
            return Response(
                {"error": f"Only {size.stock} items left in stock."}, status=400
            )
        item.save()
        return Response(CartSerializer(cart).data, status=201)

    def delete(self, request):
        cart, _ = self.get_cart_query(request)
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemDetailView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "cart"

    def get_cart_item(self, request, item_id):
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


# ── Checkout ──────────────────────────────────────────────────────────────────


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        cart = get_object_or_404(Cart, user=user)

        if not cart.items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        line_items = []
        cart_items = cart.items.select_related("product", "size")
        items_to_create = []

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

        order = Order.objects.create(user=user, status=Order.OrderStatus.PENDING)

        for item in items_to_create:
            updated = ProductSize.objects.filter(
                id=item.size.id, stock__gte=item.quantity
            ).update(stock=F("stock") - item.quantity)
            if not updated:
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

        release_unpaid_order_stock.apply_async((str(order.order_id),), countdown=1800)

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
            return Response({"error": str(e)}, status=500)


# ── Orders ────────────────────────────────────────────────────────────────────


class OrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        orders = Order.objects.filter(user=request.user)
        return Response(OrderSerializer(orders, many=True).data)


class SingleOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        order = get_object_or_404(Order, order_id=id, user=request.user)
        return Response(OrderSerializer(order).data)


# ── Stripe webhook ────────────────────────────────────────────────────────────


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
                    order = Order.objects.select_for_update().get(order_id=order_id)
                    if order.status == Order.OrderStatus.PENDING:
                        order.status = Order.OrderStatus.COMPLETED
                        order.save()
                        CartItem.objects.filter(cart__user=order.user).delete()
                except Order.DoesNotExist:
                    return Response({"error": "Order not found"}, status=404)

    return Response(status=200)
