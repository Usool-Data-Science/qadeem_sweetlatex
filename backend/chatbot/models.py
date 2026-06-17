"""
chatbot/models.py

Three tables:

1. ChatSession     — one row per conversation thread (one per user browser session)
2. ChatMessage     — individual turns within a session (user + assistant messages)
3. RAGDocument     — indexed product knowledge chunks for retrieval
                     Populated by the nightly Celery rebuild task.
"""

import uuid

from common.models import BaseModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class ChatSession(BaseModel):
    """
    A conversation thread between a user and the RAG chatbot.

    Works for both authenticated and anonymous users.
    session_key ties anonymous sessions to the same thread across page loads.
    Once a user logs in, StitchSessionView links session_key to their account.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
        null=True,
        blank=True,
        db_index=True,
    )
    session_key = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text="Anonymous session identifier — matched to user on login.",
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Auto-generated from first user message for display.",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    # Metadata for thesis evaluation
    total_turns = models.PositiveIntegerField(default=0)
    llm_provider = models.CharField(
        max_length=30,
        blank=True,
        help_text="Which LLM provider served this session: groq | openai | ollama",
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["session_key", "is_active"]),
        ]
        verbose_name = "Chat Session"

    def __str__(self):
        actor = self.user.email if self.user else f"anon:{self.session_key[:8] if self.session_key else '?'}"
        return f"{actor} — {self.title or 'Untitled'} ({self.total_turns} turns)"


class MessageRole(models.TextChoices):
    USER      = "user",      "User"
    ASSISTANT = "assistant", "Assistant"
    SYSTEM    = "system",    "System"


class ChatMessage(BaseModel):
    """
    A single turn in a ChatSession.

    Stores both the raw user query and the full assistant response, plus
    all the retrieval metadata needed for RAGAS evaluation:
      - retrieved_chunks: the exact context passages injected into the prompt
      - retrieval_scores: relevance scores per chunk
      - product_ids:      products referenced in the response
      - faithfulness / answer_relevance: computed offline by the eval pipeline
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        db_index=True,
    )
    role = models.CharField(
        max_length=10,
        choices=MessageRole.choices,
        db_index=True,
    )
    content = models.TextField()

    # RAG retrieval metadata (populated on assistant turns only)
    retrieved_chunks = models.JSONField(
        default=list,
        blank=True,
        help_text="List of {text, source, score} dicts used as context.",
    )
    retrieval_scores = models.JSONField(
        default=list,
        blank=True,
        help_text="Parallel list of retrieval relevance scores.",
    )
    referenced_product_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="UUIDs of products mentioned in this response.",
    )
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    latency_ms = models.PositiveIntegerField(default=0)

    # RAGAS evaluation metrics (populated by offline eval pipeline)
    faithfulness = models.FloatField(null=True, blank=True)
    answer_relevance = models.FloatField(null=True, blank=True)
    context_precision = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=["session", "role"]),
            models.Index(fields=["session", "created_at"]),
        ]
        verbose_name = "Chat Message"

    def __str__(self):
        preview = self.content[:60].replace("\n", " ")
        return f"[{self.role}] {preview}"


class RAGDocument(BaseModel):
    """
    A single indexed knowledge chunk for the RAG retrieval pipeline.

    One product typically generates multiple chunks:
      - title + attributes chunk  (short, factual)
      - description / composition chunk
      - review summary chunk (if reviews exist)

    The vector field stores the dense embedding from the text encoder.
    BM25 retrieval uses the raw text field.

    source_type helps the LLM ground its response:
      "product_metadata" → factual product info
      "style_guide"      → editorial content (e.g. "how to style X")
      "faq"              → store policy, sizing, shipping
    """

    class SourceType(models.TextChoices):
        PRODUCT_METADATA = "product_metadata", "Product Metadata"
        STYLE_GUIDE      = "style_guide",      "Style Guide"
        FAQ              = "faq",              "FAQ / Policy"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "core.Product",
        on_delete=models.CASCADE,
        related_name="rag_chunks",
        null=True,
        blank=True,
        help_text="Null for FAQ / style guide chunks not tied to a product.",
    )
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        db_index=True,
    )
    chunk_index = models.PositiveSmallIntegerField(
        default=0,
        help_text="Position of this chunk within its source document.",
    )
    text = models.TextField(help_text="Raw text — used for BM25 retrieval.")
    vector = models.JSONField(
        help_text="Dense embedding vector (list of floats).",
        null=True,
        blank=True,
    )
    vector_dim = models.PositiveSmallIntegerField(default=0)
    embedding_model = models.CharField(max_length=64, default="all-MiniLM-L6-v2")
    is_indexed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Flipped to True after ChromaDB ingestion.",
    )

    class Meta:
        unique_together = ("product", "source_type", "chunk_index")
        indexes = [
            models.Index(fields=["source_type", "is_indexed"]),
            models.Index(fields=["product", "source_type"]),
        ]
        verbose_name = "RAG Document Chunk"
        verbose_name_plural = "RAG Document Chunks"

    def __str__(self):
        product_title = self.product.title if self.product else "global"
        return f"{product_title} [{self.source_type}] chunk {self.chunk_index}"
