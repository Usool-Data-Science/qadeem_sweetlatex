import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core.models import Artist, Order, OrderItem, Product, ProductSize

User = get_user_model()


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="model@test.com", password="password123"
        )

        self.artist = Artist.objects.create(
            name="Modern Artist",
            description="Test description",
            website="https://artist.com",
        )

        self.product = Product.objects.create(
            title="Digital Print",
            artist=self.artist,
            goal=50,
            deadline=timezone.now() + timedelta(days=10),
            color="Blue",
            style="Abstract",
            composition="Canvas",
            price=29.99,
        )

        self.size = ProductSize.objects.create(product=self.product, size="M", stock=50)

    ## --- Product & Size Tests ---

    def test_product_str_representation(self):
        self.assertEqual(str(self.product), "Digital Print")

    def test_product_total_in_stock(self):
        ProductSize.objects.create(product=self.product, size="L", stock=30)
        self.assertEqual(self.product.total_in_stock, 80)

    def test_available_sizes(self):
        ProductSize.objects.create(product=self.product, size="L", stock=0)
        available = self.product.available_sizes
        self.assertEqual(available.count(), 1)

    def test_days_left_and_expiry(self):
        self.assertFalse(self.product.is_expired)
        self.assertGreater(self.product.days_left, 0)

    def test_stock_decrement(self):
        self.size.stock -= 5
        self.size.save()
        self.assertEqual(self.size.stock, 45)

    def test_unique_product_size_constraint(self):
        with self.assertRaises(IntegrityError):
            ProductSize.objects.create(product=self.product, size="M", stock=10)

    ## --- Order & OrderItem Tests ---

    def test_order_uuid_generation(self):
        order = Order.objects.create(user=self.user)
        self.assertIsInstance(order.order_id, uuid.UUID)

    def test_order_default_status(self):
        order = Order.objects.create(user=self.user)
        self.assertEqual(order.status, Order.OrderStatus.PENDING)

    def test_order_item_snapshot_price(self):
        order = Order.objects.create(user=self.user)

        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            size=self.size,
            quantity=2,
            price_at_purchase=self.product.price,
        )

        # Change product price
        self.product.price = 50.00
        self.product.save()

        order_item.refresh_from_db()
        self.assertEqual(float(order_item.price_at_purchase), 29.99)

    def test_order_item_subtotal(self):
        order = Order.objects.create(user=self.user)

        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            size=self.size,
            quantity=3,
            price_at_purchase=10.00,
        )

        self.assertEqual(order_item.item_subtotal, 30.00)

    def test_order_item_deleted_on_product_delete(self):
        order = Order.objects.create(user=self.user)

        OrderItem.objects.create(
            order=order,
            product=self.product,
            size=self.size,
            quantity=1,
            price_at_purchase=29.99,
        )

        self.product.delete()

        # Because CASCADE is used
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_order_item_unique_constraint(self):
        order = Order.objects.create(user=self.user)

        OrderItem.objects.create(
            order=order,
            product=self.product,
            size=self.size,
            quantity=1,
            price_at_purchase=29.99,
        )

        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(
                order=order,
                product=self.product,
                size=self.size,
                quantity=2,
                price_at_purchase=29.99,
            )

    ## --- Artist Tests ---

    def test_artist_unique_name(self):
        with self.assertRaises(IntegrityError):
            Artist.objects.create(
                name="Modern Artist", description="Another", website="https://test.com"
            )
