"""
recommendations/views.py

Five endpoints:

  GET  /api/recommendations/for-you/              — hybrid personalised feed
  GET  /api/recommendations/similar/<product_id>/ — CLIP visual similarity
  GET  /api/recommendations/trending/             — popularity-based, no auth
  POST /api/recommendations/visual-search/        — image upload → similar items
  GET  /api/recommendations/models/               — ML registry (admin only)
"""

import base64
import logging
from io import BytesIO

from PIL import Image
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from recommendations.serializers import (
    MLModelRegistrySerializer,
    RecommendedProductSerializer,
    VisualSearchSerializer,
)

logger = logging.getLogger(__name__)


def _hydrate_products(ranked: list) -> list:
    """
    Convert a list of (product_uuid_str, score) tuples into annotated
    Product objects ready for serialisation.

    Uses a single DB query with __in to avoid N+1.
    Attaches two transient attributes to each Product:
        ._first_image  — the first ProductImage row (or None)
        .score         — the fusion score from the recommendation engine
    """
    from core.models import Product, ProductImage

    if not ranked:
        return []

    pid_to_score = {str(pid): float(score) for pid, score in ranked}

    products = list(
        Product.objects.filter(product_id__in=pid_to_score.keys()).prefetch_related(
            "sizes"
        )
    )

    # Build image map with one extra query (cheaper than prefetch for this shape)
    image_map: dict = {}
    for img in ProductImage.objects.filter(product_id__in=pid_to_score.keys()).order_by(
        "created_at"
    ):
        key = str(img.product_id)
        if key not in image_map:
            image_map[key] = img

    for p in products:
        p._first_image = image_map.get(str(p.product_id))
        p.score = pid_to_score.get(str(p.product_id), 0.0)

    # Preserve ranking order from the engine
    products.sort(key=lambda p: -p.score)
    return products


class ForYouView(APIView):
    """
    GET /api/recommendations/for-you/?top_k=12

    Returns a personalised hybrid recommendation list for the authenticated
    user (BPR + SASRec + CLIP fusion).

    - Authenticated users get the full hybrid engine.
    - Anonymous users receive trending/popularity-based results.
    - Stale cached results are served immediately while a background Celery
      task refreshes them (stale-while-revalidate pattern).
    """

    permission_classes = [AllowAny]
    throttle_scope = "recommendations"

    def get(self, request):
        from ml.fusion import recommend_for_user

        from recommendations.models import RecommendationResult, RecommendationStrategy
        from recommendations.tasks import refresh_user_recommendations

        try:
            top_k = min(int(request.query_params.get("top_k", 12)), 50)
        except (ValueError, TypeError):
            top_k = 12

        user_pk = str(request.user.pk) if request.user.is_authenticated else None

        # ── Serve from cache if fresh ─────────────────────────────────────────
        if user_pk:
            cached = (
                RecommendationResult.objects.filter(
                    user_id=user_pk, anchor_product__isnull=True
                )
                .order_by("-created_at")
                .first()
            )
            if cached and not cached.is_stale:
                ranked = list(zip(cached.product_ids, cached.scores))[:top_k]
                products = _hydrate_products(ranked)
                serializer = RecommendedProductSerializer(products, many=True)
                return Response(
                    {
                        "strategy": cached.strategy,
                        "cached": True,
                        "results": serializer.data,
                    }
                )
            elif cached and cached.is_stale:
                # Kick off background refresh; fall through to live compute
                refresh_user_recommendations.delay(user_pk)

        # ── Live compute ──────────────────────────────────────────────────────
        try:
            ranked, strategy = recommend_for_user(user_pk=user_pk, top_k=top_k)
        except Exception as exc:
            logger.error("Recommendation engine error for user %s: %s", user_pk, exc)
            ranked, strategy = [], RecommendationStrategy.TRENDING

        products = _hydrate_products(ranked)
        serializer = RecommendedProductSerializer(products, many=True)
        return Response(
            {
                "strategy": strategy,
                "cached": False,
                "results": serializer.data,
            }
        )


class SimilarItemsView(APIView):
    """
    GET /api/recommendations/similar/<product_id>/?top_k=12

    Returns visually similar products for a given product using CLIP
    embeddings + FAISS ANN search.

    Used on the product detail page for the "You might also like" carousel.
    No authentication required.
    """

    permission_classes = [AllowAny]
    throttle_scope = "recommendations"

    def get(self, request, product_id):
        from ml.fusion import similar_items

        try:
            top_k = min(int(request.query_params.get("top_k", 12)), 50)
        except (ValueError, TypeError):
            top_k = 12

        try:
            ranked = similar_items(product_id=str(product_id), top_k=top_k)
        except Exception as exc:
            logger.error("Similar items error for product %s: %s", product_id, exc)
            ranked = []

        products = _hydrate_products(ranked)
        serializer = RecommendedProductSerializer(products, many=True)
        return Response(
            {
                "strategy": "similar_items",
                "results": serializer.data,
            }
        )


class TrendingView(APIView):
    """
    GET /api/recommendations/trending/?top_k=12

    Returns the most popular products based on the decayed popularity score
    computed by the Celery nightly task.

    Public endpoint — no authentication required.
    Cached at the HTTP level (Cache-Control header set).
    """

    permission_classes = [AllowAny]

    def get(self, request):
        from ml.fusion import _get_trending_ids

        try:
            top_k = min(int(request.query_params.get("top_k", 12)), 50)
        except (ValueError, TypeError):
            top_k = 12

        try:
            ranked = _get_trending_ids(top_k)
        except Exception as exc:
            logger.error("Trending fetch error: %s", exc)
            ranked = []

        products = _hydrate_products(ranked)
        serializer = RecommendedProductSerializer(products, many=True)

        response = Response(
            {
                "strategy": "trending",
                "results": serializer.data,
            }
        )
        # Cache for 10 minutes at CDN/browser level
        response["Cache-Control"] = "public, max-age=600"
        return response


class VisualSearchView(APIView):
    """
    POST /api/recommendations/visual-search/

    Accepts either a base64-encoded image or a public image URL, encodes it
    with CLIP, and returns visually similar products via FAISS.

    Request body (JSON):
        { "image_base64": "<base64 string>", "top_k": 12 }
        OR
        { "image_url": "https://...", "top_k": 12 }

    No authentication required — supports the visual search UI feature
    where shoppers can upload a photo to find matching items.
    """

    permission_classes = [AllowAny]
    throttle_scope = "recommendations"

    def post(self, request):
        from ml.clip_encoder import encode_image_from_url, encode_pil_image
        from ml.faiss_index import search

        serializer = VisualSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        vector = None

        if data.get("image_base64"):
            try:
                raw = base64.b64decode(data["image_base64"])
                image = Image.open(BytesIO(raw)).convert("RGB")
                vector = encode_pil_image(image)
            except Exception as exc:
                logger.error("Base64 image decode/encode failed: %s", exc)
                return Response(
                    {"detail": "Invalid base64 image data."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif data.get("image_url"):
            vector = encode_image_from_url(data["image_url"])

        if vector is None:
            return Response(
                {"detail": "Could not generate an embedding from the provided image."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        top_k = data.get("top_k", 12)

        try:
            ranked = search(vector, top_k=top_k)
        except Exception as exc:
            logger.error("FAISS visual search error: %s", exc)
            ranked = []

        products = _hydrate_products(ranked)
        result_serializer = RecommendedProductSerializer(products, many=True)
        return Response(
            {
                "strategy": "visual_search",
                "results": result_serializer.data,
            }
        )


class MLModelRegistryView(APIView):
    """
    GET /api/recommendations/models/

    Admin-only endpoint that exposes the full ML model registry.

    Used during thesis evaluation to track:
      - Which model checkpoints are currently active
      - Training metrics (NDCG@10, Precision@5, Recall@5) per run
      - Training duration and dataset size per checkpoint
      - Model version history for ablation study documentation
    """

    permission_classes = [IsAdminUser]

    def get(self, request):
        from recommendations.models import MLModelRegistry

        models = MLModelRegistry.objects.all().order_by("-created_at")
        serializer = MLModelRegistrySerializer(models, many=True)
        return Response(serializer.data)
