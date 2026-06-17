"""
interactions/views.py

Two endpoints:
  POST /api/interactions/log/   — frontend logs VIEW / CLICK / SEARCH events
  GET  /api/interactions/history/ — authenticated user's interaction history
                                    (used by SASRec for sequence building)

Rate-limited to prevent abuse. Anonymous users are tracked via session_key.
"""

from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from interactions.models import InteractionType, UserInteraction
from interactions.serializers import (
    UserInteractionCreateSerializer,
    UserInteractionHistorySerializer,
)
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .tasks import update_product_popularity


class LogInteractionView(APIView):
    """
    POST /api/interactions/log/

    Accepts VIEW, CLICK, and SEARCH events from the React frontend.
    Works for both authenticated users and anonymous sessions.

    Body:
        {
            "product": "<uuid>",          # omit for SEARCH events
            "interaction_type": "view",
            "session_key": "abc123",      # frontend generates this for anon users
            "metadata": {}               # optional event-specific payload
        }
    """

    permission_classes = [AllowAny]
    throttle_scope = "interaction_log"  # 120/min in settings

    @method_decorator(never_cache)
    def post(self, request):
        serializer = UserInteractionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interaction = serializer.save(
            user=request.user if request.user.is_authenticated else None,
        )

        # Async: update popularity score for this product
        if interaction.product_id:
            update_product_popularity.delay(str(interaction.product_id))

        return Response({"logged": True}, status=status.HTTP_201_CREATED)


class InteractionHistoryView(APIView):
    """
    GET /api/interactions/history/?type=view&limit=50

    Returns the authenticated user's interaction sequence, ordered by time.
    The ML pipeline reads this to build the SASRec input sequence.

    Query params:
        type   — filter by interaction_type (optional)
        limit  — max rows, default 100, max 500
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            UserInteraction.objects.filter(user=request.user)
            .select_related("product")
            .order_by("-created_at")
        )

        interaction_type = request.query_params.get("type")
        if interaction_type and interaction_type in InteractionType.values:
            qs = qs.filter(interaction_type=interaction_type)

        try:
            limit = min(int(request.query_params.get("limit", 100)), 500)
        except (ValueError, TypeError):
            limit = 100

        qs = qs[:limit]
        serializer = UserInteractionHistorySerializer(qs, many=True)
        return Response(serializer.data)


class StitchSessionView(APIView):
    """
    POST /api/interactions/stitch/

    Called once at login to reassign anonymous session interactions to the
    newly authenticated user.  Prevents cold-start for users who browsed
    before signing in.

    Body: { "session_key": "abc123" }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_key = request.data.get("session_key", "").strip()
        if not session_key:
            return Response(
                {"detail": "session_key required."}, status=status.HTTP_400_BAD_REQUEST
            )

        updated = UserInteraction.objects.filter(
            session_key=session_key, user__isnull=True
        ).update(user=request.user)
        return Response({"stitched": updated})
