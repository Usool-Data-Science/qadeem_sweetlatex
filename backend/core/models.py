import uuid

from accounts.models import Address
from common.models import BaseModel
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Artist(BaseModel):
    """Model representing an artist."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    website = models.URLField()

    def __str__(self):
        return self.name


class ArtistImage(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artist = models.OneToOneField(
        Artist, on_delete=models.CASCADE, related_name="image"
    )
    image = models.ImageField(upload_to="temp/", null=True, blank=True)
    image_url = models.URLField(blank=True)
    public_id = models.CharField(max_length=255, blank=True)


class Product(BaseModel):
    """Model representing a product created by an artist."""

    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(
        Artist, on_delete=models.CASCADE, related_name="products", db_index=True
    )
    goal = models.PositiveIntegerField()
    deadline = models.DateTimeField()
    color = models.CharField(max_length=50)
    style = models.CharField(max_length=50)
    composition = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def available_sizes(self):
        return self.sizes.filter(stock__gt=0)

    @property
    def days_left(self):
        """Calculate the number of days left until the deadline."""
        remaining_time = self.deadline - timezone.now()
        return max(remaining_time.days, 0)

    @property
    def is_expired(self):
        return self.days_left <= 0

    @property
    def total_in_stock(self):
        from django.db.models import Sum

        return self.sizes.aggregate(total=Sum("stock"))["total"] or 0

    @property
    def is_sold_out(self):
        return self.total_in_stock == 0

    def __str__(self):
        return self.title


class ProductSize(BaseModel):
    SIZE_CHOICES = [
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
        ("XL", "Extra Large"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sizes")
    size = models.CharField(max_length=5, choices=SIZE_CHOICES)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.title} - {self.size}"

    class Meta:
        unique_together = ("product", "size")


class ProductImage(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="temp/", null=True, blank=True)
    image_url = models.URLField(blank=True)
    public_id = models.CharField(max_length=255, blank=True)
    # is_main = models.BooleanField()

    def __str__(self):
        return f"{self.product.title} Image"


class OrderItem(BaseModel):
    """Model representing an item in an order."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="items")
    quantity = models.PositiveIntegerField()
    size = models.ForeignKey(ProductSize, on_delete=models.CASCADE)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def item_subtotal(self):
        """Calculate the total price for this order item."""
        return self.quantity * self.price_at_purchase

    def __str__(self):
        return f"{self.quantity} x {self.product.title} (Size: {self.size})"

    class Meta:
        unique_together = ("product", "size", "order")


class Order(BaseModel):
    """Model representing an order for a product."""

    class OrderStatus(models.TextChoices):
        PENDING = "Pending"
        COMPLETED = "Completed"
        CANCELLED = "Cancelled"

    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    products = models.ManyToManyField(
        Product, through="OrderItem", related_name="orders"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
    )
    address = models.ForeignKey(
        Address, null=True, on_delete=models.SET_NULL, related_name="orders"
    )

    def __str__(self):
        return f"Order {self.order_id} for {self.user.email}"


class Cart(BaseModel):
    """Model representing a shopping cart for a user."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="cart", null=True, blank=True
    )
    session_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    products = models.ManyToManyField(Product, through="CartItem", related_name="carts")

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Cart for {self.session_id}"

    @property
    def total_price(self):
        from django.db.models import F, Sum

        # Calculate on the DB level instead of a Python loop
        return (
            self.items.aggregate(total=Sum(F("quantity") * F("product__price")))[
                "total"
            ]
            or 0
        )


class CartItem(BaseModel):
    """Model representing an item in a shopping cart."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    quantity = models.PositiveIntegerField()
    # This is already handled by product above, so we need to avoid integrity error
    size = models.ForeignKey(ProductSize, on_delete=models.SET_NULL, null=True)

    @property
    def item_subtotal(self):
        """Calculate the total price for this cart item."""
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.quantity} x {self.product.title} (Size: {self.size})"

    class Meta:
        unique_together = ("cart", "product", "size")
