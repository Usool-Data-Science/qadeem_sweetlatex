from django.urls import path

from .views import (
    ArtistView,
    CartItemDetailView,
    CartView,
    CheckoutView,
    ContactView,
    OrderView,
    ProductListView,
    SingleArtistView,
    SingleOrderView,
    SingleProductView,
    stripe_webhook,
)

urlpatterns = [
    # --- General ---
    path("contact-us/", ContactView.as_view(), name="contact-us"),
    # --- Products ---
    # GET (all) or POST (create new)
    path("products/", ProductListView.as_view(), name="products-list"),
    path("products/<uuid:id>/", SingleProductView.as_view(), name="product-detail"),
    # --- Artists ---
    path("artists/", ArtistView.as_view(), name="list_artists"),
    path(
        "artists/create/", SingleArtistView.as_view(), name="create_artist"
    ),  # POST logic
    path(
        "artists/<int:id>/", SingleArtistView.as_view(), name="artist_detail"
    ),  # GET/PUT/PATCH/DELETE
    # --- Cart ---
    path("cart/", CartView.as_view(), name="cart_summary"),
    # For incrementing/decrementing/deleting specific items in cart
    path(
        "cart/item/<int:item_id>/",
        CartItemDetailView.as_view(),
        name="cart_item_detail",
    ),
    # --- Checkout & Payments ---
    path("orders/", OrderView.as_view(), name="get_all_user_orders"),
    path("orders/<uuid:id>/", SingleOrderView.as_view(), name="get_order_detail"),
    # --- Checkout & Payments ---
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
]
