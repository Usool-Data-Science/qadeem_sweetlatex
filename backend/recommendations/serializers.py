from rest_framework import serializers

from recommendations.models import MLModelRegistry, RecommendationResult


class RecommendedProductSerializer(serializers.Serializer):
    """
    Lightweight representation of a recommended product.
    Full product detail is fetched client-side via /api/core/products/<id>/.
    """

    product_id = serializers.UUIDField()
    score = serializers.FloatField()
    title = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    image_url = serializers.SerializerMethodField()
    style = serializers.CharField()
    color = serializers.CharField()
    is_sold_out = serializers.BooleanField()

    def get_image_url(self, obj):
        first_image = getattr(obj, "_first_image", None)
        return first_image.image_url if first_image else None


class RecommendationResultSerializer(serializers.ModelSerializer):
    products = RecommendedProductSerializer(
        many=True, read_only=True, source="_hydrated_products"
    )
    is_stale = serializers.BooleanField(read_only=True)

    class Meta:
        model = RecommendationResult
        fields = ["id", "strategy", "products", "is_stale", "expires_at"]


class VisualSearchSerializer(serializers.Serializer):
    """
    Accepts a base64-encoded image or a URL for visual similarity search.
    Exactly one of image_base64 or image_url must be provided.
    """

    image_base64 = serializers.CharField(required=False, allow_blank=True)
    image_url = serializers.CharField(required=False, allow_blank=True)
    top_k = serializers.IntegerField(min_value=1, max_value=50, default=12)

    def validate(self, attrs):
        if not attrs.get("image_base64") and not attrs.get("image_url"):
            raise serializers.ValidationError(
                "Provide either image_base64 or image_url."
            )
        return attrs


class MLModelRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModelRegistry
        fields = [
            "id",
            "model_type",
            "version",
            "is_active",
            "metrics",
            "trained_on_rows",
            "training_duration_seconds",
            "created_at",
        ]
