from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from tasks.tasks import release_unpaid_order_stock

from core.models import Artist, Order, OrderItem, Product, ProductSize

User = get_user_model()


class TaskTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="task@test.com", password="password123"
        )

        self.artist = Artist.objects.create(
            name="Task Artist", description="Test artist", website="https://artist.com"
        )

        self.product = Product.objects.create(
            title="Test Product",
            artist=self.artist,
            goal=10,
            deadline=timezone.now() + timedelta(days=5),
            color="Red",
            style="Modern",
            composition="Canvas",
            price=10.00,
        )

        self.size = ProductSize.objects.create(
            product=self.product,
            size="M",
            stock=5,  # already deducted stock scenario
        )

    def test_release_stock_task(self):
        """Ensure stock is restored and order is cancelled."""

        # Simulate an unpaid order
        order = Order.objects.create(user=self.user, status=Order.OrderStatus.PENDING)

        OrderItem.objects.create(
            order=order,
            product=self.product,
            size=self.size,
            quantity=3,
            price_at_purchase=10.00,
        )

        # Run task synchronously
        release_unpaid_order_stock(str(order.order_id))

        # Assert stock restored
        self.size.refresh_from_db()
        self.assertEqual(self.size.stock, 8)  # 5 + 3

        # Assert order cancelled
        order.refresh_from_db()
        self.assertEqual(order.status, Order.OrderStatus.CANCELLED)
