"""
recommendations/models.py

Three tables:

1. ProductEmbedding  — stores CLIP visual + text vectors per product.
                       FAISS index is built from these rows nightly.

2. RecommendationResult — cached recommendation lists per (user, strategy).
                          TTL-invalidated by Celery. Avoids recomputing on
                          every page load.

3. MLModelRegistry  — tracks which SASRec / BPR checkpoint is currently live,
                       enabling zero-downtime model swaps and rollback.
"""

import uuid

from common.models import BaseModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class EmbeddingSource(models.TextChoices):
    CLIP_IMAGE = "clip_image", "CLIP Image Embedding"
    SBERT_TEXT = "sbert_text", "Sentence-BERT Text Embedding"
    CLIP_FUSED = "clip_fused", "CLIP Image + Text Fused"


class ProductEmbedding(BaseModel):
    """
    Stores the latest embedding vector for a product.

    One row per (product, source) combination.
    The embedding is serialised as a JSON list of floats — clean and
    portable without requiring pgvector at this stage.  When pgvector is
    available (docker-compose adds the extension), migrate to VectorField.

    CLIP ViT-B/32  → 512 dimensions
    SBERT (all-MiniLM-L6-v2) → 384 dimensions
    Fused (concat + PCA) → 512 dimensions
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    product = models.ForeignKey(
        "core.Product",
        on_delete=models.CASCADE,
        related_name="embeddings",
        db_index=True,
    )
    source = models.CharField(
        max_length=20,
        choices=EmbeddingSource.choices,
        db_index=True,
    )
    vector = models.JSONField(
        help_text="Float list — CLIP: 512-d, SBERT: 384-d, fused: 512-d"
    )
    vector_dim = models.PositiveSmallIntegerField()
    model_version = models.CharField(
        max_length=64,
        default="v1",
        help_text="Bumped when embedding model changes, triggers FAISS rebuild.",
    )

    class Meta:
        unique_together = ("product", "source")
        indexes = [
            models.Index(fields=["source", "model_version"]),
        ]
        verbose_name = "Product Embedding"
        verbose_name_plural = "Product Embeddings"

    def __str__(self):
        return f"{self.product.title} [{self.source}] dim={self.vector_dim}"


class RecommendationStrategy(models.TextChoices):
    FOR_YOU = "for_you", "Personalised For You"
    SIMILAR_ITEMS = "similar_items", "Similar Items (Visual)"
    TRENDING = "trending", "Trending / Popular"
    SEQUENTIAL = "sequential", "Sequential (SASRec)"
    HYBRID = "hybrid", "Hybrid Fusion"
    COLD_START = "cold_start", "Cold-Start Fallback"


class RecommendationResult(BaseModel):
    """
    Cached recommendation list for a user + strategy pair.

    product_ids is an ordered JSON list of product UUIDs (strings),
    ranked highest-first.  The frontend fetches full product details
    in a separate /api/core/products/bulk/ call to keep this payload small.

    expires_at is set by the Celery task that populates this row.
    The /api/recommendations/ view checks it and triggers a background
    refresh if stale rather than blocking the request.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recommendation_results",
        null=True,
        blank=True,
        db_index=True,
        help_text="Null for TRENDING / COLD_START strategies.",
    )
    # For SIMILAR_ITEMS, anchor_product holds the reference product
    anchor_product = models.ForeignKey(
        "core.Product",
        on_delete=models.CASCADE,
        related_name="similar_results",
        null=True,
        blank=True,
    )
    strategy = models.CharField(
        max_length=20,
        choices=RecommendationStrategy.choices,
        db_index=True,
    )
    product_ids = models.JSONField(
        help_text="Ordered list of product UUID strings, best first."
    )
    scores = models.JSONField(
        default=list,
        help_text="Parallel list of fusion scores for evaluation logging.",
    )
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        unique_together = ("user", "anchor_product", "strategy")
        indexes = [
            models.Index(fields=["strategy", "expires_at"]),
            models.Index(fields=["user", "strategy"]),
        ]
        verbose_name = "Recommendation Result"

    def __str__(self):
        actor = self.user.email if self.user else "global"
        return f"{actor} | {self.strategy} | {len(self.product_ids)} items"

    @property
    def is_stale(self):
        from django.utils import timezone

        return timezone.now() >= self.expires_at


class MLModelRegistry(BaseModel):
    """
    Tracks which ML model checkpoint is currently live.

    Enables:
      - Zero-downtime model swap (set is_active=False on old, True on new)
      - Rollback (flip is_active)
      - Thesis evaluation (record metrics alongside the checkpoint)
    """

    class ModelType(models.TextChoices):
        SASREC = "sasrec", "SASRec Sequential"
        BPR = "bpr", "BPR Matrix Factorisation"
        CLIP = "clip", "CLIP Visual Encoder"
        RERANKER = "reranker", "Cross-Encoder Reranker"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_type = models.CharField(max_length=20, choices=ModelType.choices)
    version = models.CharField(max_length=64)
    artifact_path = models.CharField(
        max_length=512,
        help_text="Absolute container path or S3 URI to the checkpoint file.",
    )
    is_active = models.BooleanField(default=False, db_index=True)

    # Evaluation metrics captured at training time
    metrics = models.JSONField(
        default=dict,
        help_text="e.g. {'ndcg@10': 0.42, 'recall@5': 0.31, 'precision@5': 0.28}",
    )
    trained_on_rows = models.PositiveIntegerField(default=0)
    training_duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["model_type", "is_active"])]
        verbose_name = "ML Model Registry Entry"
        verbose_name_plural = "ML Model Registry"

    def __str__(self):
        active = "✓" if self.is_active else "✗"
        return f"[{active}] {self.model_type} v{self.version}"
