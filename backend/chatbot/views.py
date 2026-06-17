"""
chatbot/views.py

Three endpoints:

  POST /api/chatbot/chat/           — main chat endpoint (streaming SSE)
  GET  /api/chatbot/sessions/       — list user's chat sessions
  GET  /api/chatbot/sessions/<id>/  — retrieve a full session with messages
"""

import json
import logging

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from chatbot.serializers import (
    ChatMessageSerializer,
    ChatQuerySerializer,
    ChatSessionSerializer,
)

logger = logging.getLogger(__name__)


class ChatView(APIView):
    """
    POST /api/chatbot/chat/

    Main RAG chatbot endpoint. Streams the LLM response token-by-token
    using Server-Sent Events so the React frontend can render text as it arrives.

    Request body:
        {
            "message":     "Show me red summer dresses under £50",
            "session_id":  "<uuid>",    // optional — omit to start a new session
            "session_key": "abc123"     // for anonymous users
        }

    Response: text/event-stream
        data: {"token": "Here"}
        data: {"token": " are"}
        data: {"token": " some..."}
        data: {"done": true, "message_id": "<uuid>", "product_ids": [...]}
    """

    permission_classes = [AllowAny]
    throttle_scope = "chatbot"

    def post(self, request):
        serializer = ChatQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user if request.user.is_authenticated else None
        session = self._get_or_create_session(
            user=user,
            session_id=data.get("session_id"),
            session_key=data.get("session_key", ""),
        )

        # Save the user message immediately
        user_message = self._save_message(session, "user", data["message"])

        # Build conversation history for multi-turn context
        history = list(
            session.messages
            .exclude(id=user_message.id)
            .order_by("-created_at")[:6]
            .values("role", "content")
        )
        history.reverse()

        def event_stream():
            from chatbot.models import ChatMessage
            from ml.rag_pipeline import generate, retrieve

            # Retrieve relevant chunks
            chunks = retrieve(data["message"], top_k=5)

            full_response = ""
            meta = {}

            gen = generate(
                query=data["message"],
                context_chunks=chunks,
                conversation_history=history,
                user=user,
                stream=True,
            )

            try:
                for token in gen:
                    if isinstance(token, str):
                        full_response += token
                        payload = json.dumps({"token": token})
                        yield f"data: {payload}\n\n"
                    elif isinstance(token, dict):
                        meta = token
            except StopIteration as e:
                meta = e.value or {}

            # Persist the assistant message with all RAG metadata
            assistant_msg = ChatMessage.objects.create(
                session=session,
                role="assistant",
                content=full_response,
                retrieved_chunks=[
                    {"text": c["text"], "source_type": c.get("source_type", ""), "score": c.get("rrf_score", 0)}
                    for c in chunks
                ],
                retrieval_scores=[c.get("rrf_score", 0) for c in chunks],
                referenced_product_ids=meta.get("product_ids", []),
                prompt_tokens=meta.get("prompt_tokens", 0),
                completion_tokens=meta.get("completion_tokens", 0),
                latency_ms=meta.get("latency_ms", 0),
            )

            # Update session metadata
            session.total_turns += 1
            session.llm_provider = meta.get("provider", "")
            if not session.title and len(data["message"]) > 0:
                session.title = data["message"][:80]
            session.save(update_fields=["total_turns", "llm_provider", "title"])

            # Send final done event with message ID and referenced products
            done_payload = json.dumps({
                "done":        True,
                "message_id":  str(assistant_msg.id),
                "product_ids": meta.get("product_ids", []),
            })
            yield f"data: {done_payload}\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"  # Disable Nginx buffering
        return response

    def _get_or_create_session(self, user, session_id, session_key):
        from chatbot.models import ChatSession

        if session_id:
            try:
                filters = {"id": session_id, "is_active": True}
                if user:
                    filters["user"] = user
                else:
                    filters["session_key"] = session_key
                return ChatSession.objects.get(**filters)
            except ChatSession.DoesNotExist:
                pass

        return ChatSession.objects.create(
            user=user,
            session_key=session_key if not user else None,
        )

    def _save_message(self, session, role, content):
        from chatbot.models import ChatMessage
        return ChatMessage.objects.create(
            session=session,
            role=role,
            content=content,
        )


class ChatSessionListView(APIView):
    """
    GET /api/chatbot/sessions/

    Returns the authenticated user's chat session list (without messages).
    Used to render the chat history sidebar in the frontend.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = (
            request.user.chat_sessions
            .filter(is_active=True)
            .order_by("-created_at")[:20]
        )
        serializer = ChatSessionSerializer(sessions, many=True)
        return Response(serializer.data)


class ChatSessionDetailView(APIView):
    """
    GET  /api/chatbot/sessions/<session_id>/  — full session with all messages
    DELETE /api/chatbot/sessions/<session_id>/ — soft-delete (is_active=False)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        try:
            session = request.user.chat_sessions.get(id=session_id, is_active=True)
        except Exception:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChatSessionSerializer(session)
        return Response(serializer.data)

    def delete(self, request, session_id):
        try:
            session = request.user.chat_sessions.get(id=session_id)
            session.is_active = False
            session.save(update_fields=["is_active"])
        except Exception:
            return Response({"detail": "Session not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)
