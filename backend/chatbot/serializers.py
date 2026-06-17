from rest_framework import serializers

from chatbot.models import ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ChatMessage
        fields = [
            "id", "role", "content",
            "referenced_product_ids",
            "latency_ms", "created_at",
        ]


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model  = ChatSession
        fields = ["id", "title", "total_turns", "messages", "created_at"]


class ChatQuerySerializer(serializers.Serializer):
    """Validates an incoming chat message from the frontend."""
    message     = serializers.CharField(max_length=2000)
    session_id  = serializers.UUIDField(required=False, allow_null=True)
    session_key = serializers.CharField(required=False, allow_blank=True)
