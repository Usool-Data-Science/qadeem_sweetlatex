"""
interactions/models.py

Tracks every meaningful user signal: product views, clicks, wishlist adds,
cart additions, and purchases.  These events feed:
  - Collaborative filtering (BPR / SASRec)
  - RAG chatbot context (what the user has been looking at)
  - Cold-start fallback (popularity scoring)

Design notes:
  - All events are append-only; we never update or delete rows so the full
    temporal sequence is always available for SASRec.
  - session_key supports anonymous users (pre-login) so we can stitch
    sessions together once the user authenticates.
  - product_vector_version lets us invalidate FAISS neighbours when we
    retrain CLIP embeddings.
"""

import uuid

from common.models import BaseModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class InteractionType(models.TextChoices):
    VIEW = "view", "Product View"
    CLICK = "click", "Product Click"
    WISHLIST = "wishlist", "Added to Wishlist"
    CART_ADD = "cart_add", "Added to Cart"
    CART_REMOVE = "cart_remove", "Removed from Cart"
    PURCHASE = "purchase", "Purchased"
    SEARCH = "search", "Search Query"
    CHAT = "chat", "Chatbot Interaction"


class UserInteraction(BaseModel):
    """
    Append-only log of every user–product signal.

    Indexes:
      - (user, interaction_type) — fast CF queries per event type
      - (user, created_at)       — time-ordered sequence for SASRec
      - (product, interaction_type) — item popularity scoring
      - session_key              — anonymous session stitching
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Actor — one of user or session_key will always be set
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="interactions",
        null=True,
        blank=True,
        db_index=True,
    )
    session_key = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text="Anonymous session key — populated before login.",
    )

    # Subject
    product = models.ForeignKey(
        "core.Product",
        on_delete=models.CASCADE,
        related_name="interactions",
        null=True,
        blank=True,
        db_index=True,
    )

    interaction_type = models.CharField(
        max_length=20,
        choices=InteractionType.choices,
        db_index=True,
    )

    # Metadata — flexible JSON payload per event type
    # For SEARCH: {"query": "...", "results_count": N}
    # For CHAT:   {"query": "...", "intent": "...", "products_returned": [...]}
    # For VIEW:   {"duration_seconds": N, "scroll_depth": 0.0-1.0}
    metadata = models.JSONField(default=dict, blank=True)

    # Implicit feedback weight (1.0 for view, 2.0 for cart, 5.0 for purchase)
    # Pre-computed here so CF trainer can do a single DB read
    weight = models.FloatField(default=1.0)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "interaction_type"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["product", "interaction_type"]),
            models.Index(fields=["session_key", "created_at"]),
        ]
        verbose_name = "User Interaction"
        verbose_name_plural = "User Interactions"

    def __str__(self):
        actor = self.user or self.session_key or "anon"
        return f"{actor} → {self.interaction_type} → {self.product_id}"


# ── Interaction weights ────────────────────────────────────────────────────────
INTERACTION_WEIGHTS: dict[str, float] = {
    InteractionType.VIEW: 1.0,
    InteractionType.CLICK: 1.5,
    InteractionType.WISHLIST: 2.0,
    InteractionType.CART_ADD: 3.0,
    InteractionType.CART_REMOVE: 0.5,
    InteractionType.PURCHASE: 5.0,
    InteractionType.SEARCH: 0.5,
    InteractionType.CHAT: 1.0,
}


class ProductPopularityScore(BaseModel):
    """
    Materialised popularity score per product — updated hourly by Celery.
    Used as the cold-start fallback when a user has < 5 interactions.

    score = Σ (interaction_weight × recency_decay) over rolling 30-day window
    """

    product = models.OneToOneField(
        "core.Product",
        on_delete=models.CASCADE,
        related_name="popularity",
    )
    score = models.FloatField(default=0.0, db_index=True)
    view_count = models.PositiveIntegerField(default=0)
    purchase_count = models.PositiveIntegerField(default=0)
    cart_add_count = models.PositiveIntegerField(default=0)
    last_computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-score",)
        verbose_name = "Product Popularity Score"

    def __str__(self):
        return f"{self.product.title} — score: {self.score:.2f}"


class SearchQuery(BaseModel):
    """
    Stores deduplicated search queries with result counts.
    Used to:
      - Pre-warm RAG vector store for common queries
      - Analyse user intent for thesis evaluation
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="searches",
    )
    session_key = models.CharField(max_length=64, null=True, blank=True)
    query_text = models.TextField()
    results_count = models.PositiveIntegerField(default=0)
    source = models.CharField(
        max_length=20,
        choices=[
            ("search_bar", "Search Bar"),
            ("chatbot", "Chatbot"),
            ("visual", "Visual Search"),
        ],
        default="search_bar",
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["query_text"])]

    def __str__(self):
        return f'"{self.query_text[:60]}" ({self.source})'
