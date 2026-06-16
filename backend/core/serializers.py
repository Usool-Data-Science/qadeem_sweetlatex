from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from .models import Artist, Cart, CartItem, Order, OrderItem, Product, ProductSize


class ArtistSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = ["id", "name", "image", "description", "website"]

    def get_image(self, obj):
        return obj.image.image_url


class ProductSerializer(serializers.ModelSerializer):
    available_sizes = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    artist_name = serializers.CharField(source="artist.name")
    artist_details = serializers.CharField(source="artist.description")

    class Meta:
        model = Product
        fields = [
            "product_id",
            "title",
            "price",
            "goal",
            "artist_name",
            "artist_details",
            "images",
            "color",
            "days_left",
            "is_expired",
            "total_in_stock",
            "is_sold_out",
            "composition",
            "available_sizes",
        ]

    def get_available_sizes(self, obj):
        return [s.size for s in obj.available_sizes]

    def get_images(self, obj):
        return [image.image_url for image in obj.images.all()]

    def validate_price(self, value):
        """Ensures the price is not lesser than or equal to zero"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value


class ProductInfoSerializer(serializers.Serializer):
    """
    Return all products, count of products and max price
    """

    products = ProductSerializer(many=True)
    count = serializers.IntegerField()
    max_price = serializers.FloatField()
    min_price = serializers.FloatField()


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.title", read_only=True)
    product_image = serializers.SerializerMethodField()

    price = serializers.DecimalField(
        source="price_at_purchase",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    size_name = serializers.CharField(source="size.size", read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_name",
            "product_image",
            "size_name",
            "quantity",
            "price",
            "item_subtotal",
        ]

    def get_product_image(self, obj):
        first_image = obj.product.images.first()

        if first_image and first_image.image:
            return first_image.image.url

        return None


class OrderSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.CharField(source="user.email", read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, obj):
        order_items = obj.items.all()
        total_price = sum(item.item_subtotal for item in order_items)
        return total_price

    class Meta:
        model = Order
        fields = ["order_id", "user", "total_price", "created_at", "items"]


class OrderCreateSerializer(serializers.ModelSerializer):
    class OrderItemCreateSerializer(serializers.ModelSerializer):
        # We use PrimaryKeyRelatedField to ensure the user sends a valid Size ID
        size = serializers.PrimaryKeyRelatedField(queryset=ProductSize.objects.all())

        class Meta:
            model = OrderItem
            fields = ("product", "quantity", "size")

    order_id = serializers.UUIDField(read_only=True)
    items = OrderItemCreateSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must have at least one item.")

        # Check for duplicate product-size combos in the request
        seen = set()
        for item in value:
            combo = (item["product"].pk, item["size"].pk)
            if combo in seen:
                raise serializers.ValidationError(
                    f"Duplicate item for {item['product'].title} in order."
                )
            seen.add(combo)
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        user = self.context["request"].user  # Assumes user is authenticated

        with transaction.atomic():
            # 1. Create the Order
            order = Order.objects.create(user=user, **validated_data)

            for item_data in items_data:
                product = item_data["product"]
                quantity = item_data["quantity"]
                product_size = item_data["size"]

                # 2. Validation: Ensure size belongs to the product
                if product_size.product != product:
                    raise serializers.ValidationError(
                        f"Size {product_size.size} does not belong to product {product.title}"
                    )

                # 3. Validation: Check Stock
                if product_size.stock < quantity:
                    raise serializers.ValidationError(
                        f"Not enough stock for {product.title} (Size: {product_size.size}). "
                        f"Available: {product_size.stock}"
                    )

                # 4. Atomic Stock Deduction (Prevents Race Conditions)
                # Using .filter().update() with F() is safer for high-concurrency
                updated_count = ProductSize.objects.filter(
                    pk=product_size.pk, stock__gte=quantity
                ).update(stock=F("stock") - quantity)

                if not updated_count:
                    raise serializers.ValidationError(
                        f"Stock changed during transaction for {product.title}"
                    )

                # 5. Create OrderItem with Price Snapshot
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    size=product_size,
                    price_at_purchase=product.price,  # Critical for accounting
                )

            return order

    class Meta:
        model = Order
        fields = ("order_id", "user", "status", "items")
        extra_kwargs = {"user": {"read_only": True}}


class cartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.CharField(source="product.product_id", read_only=True)
    product_name = serializers.CharField(source="product.title", read_only=True)
    product_image = serializers.SerializerMethodField()
    product_price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2, read_only=True
    )
    size = serializers.CharField(source="size.size", read_only=True)

    def get_product_image(self, obj):
        first_image = obj.product.images.first()
        return first_image.image_url if first_image else None

    class Meta:
        model = CartItem
        fields = [
            "id",
            "quantity",
            "item_subtotal",
            "product_name",
            "product_price",
            "product_id",
            "product_image",
            "size",
        ]


class CartSerializer(serializers.ModelSerializer):
    items = cartItemSerializer(many=True, read_only=True)
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return obj.user.email if obj.user else None

    class Meta:
        model = Cart
        fields = ["id", "user", "total_price", "created_at", "items"]
