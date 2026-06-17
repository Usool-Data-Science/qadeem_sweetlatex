from django.contrib import admin

from chatbot.models import ChatMessage, ChatSession, RAGDocument


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display  = ["id", "actor", "title", "total_turns", "llm_provider", "is_active", "created_at"]
    list_filter   = ["is_active", "llm_provider", "created_at"]
    search_fields = ["user__email", "session_key", "title"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def actor(self, obj):
        return obj.user.email if obj.user else f"anon:{(obj.session_key or '')[:8]}"
    actor.short_description = "User"


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display  = ["id", "session", "role", "preview", "latency_ms", "faithfulness", "created_at"]
    list_filter   = ["role", "created_at"]
    search_fields = ["content", "session__user__email"]
    readonly_fields = ["id", "created_at"]

    def preview(self, obj):
        return obj.content[:80]
    preview.short_description = "Content preview"


@admin.register(RAGDocument)
class RAGDocumentAdmin(admin.ModelAdmin):
    list_display  = ["id", "product", "source_type", "chunk_index", "is_indexed", "embedding_model"]
    list_filter   = ["source_type", "is_indexed", "embedding_model"]
    search_fields = ["text", "product__title"]
    readonly_fields = ["id", "created_at"]
