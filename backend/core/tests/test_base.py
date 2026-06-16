from unittest import skip
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Artist, Cart, CartItem, Order, Product, ProductSize

User = get_user_model()


class CheckoutTests(APITestCase):
    def setUp(self):
        # 1. Create User
        self.user = User.objects.create_user(
            email="test@example.com", password="password123"
        )
        self.client.force_authenticate(user=self.user)

        # 2. Create Artist
        self.artist = Artist.objects.create(
            name="Picasso", description="Painter", website="https://picasso.com"
        )

        # 3. Create Product
        self.product = Product.objects.create(
            title="Blue Canvas",
            artist=self.artist,
            goal=100,
            deadline="2026-12-31T00:00:00Z",
            price=50.00,
        )

        # 4. Create Sizes
        self.size_small = ProductSize.objects.create(
            product=self.product, size="S", stock=10
        )

        # 5. Setup Cart
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(
            cart=self.cart, product=self.product, size=self.size_small, quantity=2
        )

        self.checkout_url = reverse("checkout")

    @patch("stripe.checkout.Session.create")
    @patch("tasks.tasks.release_unpaid_order_stock.apply_async")
    def test_successful_checkout_reserves_stock(self, mock_celery, mock_stripe):
        """Test that checkout creates an order, deducts stock, and calls Stripe."""

        # Mock Stripe response
        mock_stripe.return_value.url = "https://checkout.stripe.com/test"

        response = self.client.post(self.checkout_url)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("session_url", response.data)

        # Check stock deduction (Original 10 - 2 in cart = 8)
        self.size_small.refresh_from_db()
        self.assertEqual(self.size_small.stock, 8)

        # Check Order Creation
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.status, Order.OrderStatus.PENDING)

        # Check OrderItem Snapshot Price
        order_item = order.items.first()
        self.assertEqual(order_item.price_at_purchase, 50.00)

        # Check Celery task was scheduled
        mock_celery.assert_called_once()

    def test_checkout_fails_if_insufficient_stock(self):
        """Test that checkout blocks orders if stock is too low."""
        # Update cart quantity to exceed stock
        self.cart_item.quantity = 20
        self.cart_item.save()

        response = self.client.post(self.checkout_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Insufficient stock", response.data["error"])

        # Ensure no order was created
        self.assertEqual(Order.objects.count(), 0)

    @skip("Requires complex mocking of Stripe API and transaction rollback")
    @patch("stripe.checkout.Session.create")
    def test_checkout_rollback_on_stripe_error(self, mock_stripe):
        """Ensure stock is restored if Stripe session creation fails."""
        mock_stripe.side_effect = Exception("Stripe Connection Failed")

        response = self.client.post(self.checkout_url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Stock should still be 10 because transaction.atomic rolled back the deduction
        self.size_small.refresh_from_db()
        self.assertEqual(self.size_small.stock, 10)

        # Order should not exist
        self.assertEqual(Order.objects.count(), 0)
