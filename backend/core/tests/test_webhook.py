from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import (
    Artist,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Product,
    ProductSize,
)

User = get_user_model()


class WebhookTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="buyer@example.com", password="password"
        )

        self.artist = Artist.objects.create(
            name="Webhook Artist",
            description="Artist for webhook test",
            website="https://artist.com",
        )

        self.product = Product.objects.create(
            title="Test Product",
            artist=self.artist,
            goal=10,
            deadline=timezone.now() + timedelta(days=5),
            color="Black",
            style="Modern",
            composition="Canvas",
            price=10.00,
        )

        self.size = ProductSize.objects.create(product=self.product, size="M", stock=10)

        self.order = Order.objects.create(
            user=self.user, status=Order.OrderStatus.PENDING
        )

        # Link order to product
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            size=self.size,
            quantity=1,
            price_at_purchase=10.00,
        )

        self.cart = Cart.objects.create(user=self.user)

        CartItem.objects.create(
            cart=self.cart, product=self.product, size=self.size, quantity=1
        )

        self.webhook_url = reverse("stripe-webhook")

    @patch("stripe.Webhook.construct_event")
    def test_webhook_completes_order_and_clears_cart(self, mock_webhook):
        """Valid Stripe event → order COMPLETED + cart cleared."""

        mock_webhook.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {"order_id": str(self.order.order_id)}}},
        }

        response = self.client.post(self.webhook_url, data={}, format="json")

        self.assertEqual(response.status_code, 200)

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.OrderStatus.COMPLETED)

        # Cart should be emptied
        self.assertEqual(self.cart.items.count(), 0)
