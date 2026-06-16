from interactions.models import InteractionType, UserInteraction
from rest_framework import serializers


class UserInteractionCreateSerializer(serializers.ModelSerializer):
    """
    Used by the frontend to log VIEW and CLICK events.
    PURCHASE / CART_ADD / CART_REMOVE are handled by signals, not this endpoint.
    """

    ALLOWED_TYPES = {
        InteractionType.VIEW,
        InteractionType.CLICK,
        InteractionType.SEARCH,
    }

    interaction_type = serializers.ChoiceField(choices=InteractionType.choices)
    session_key = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = UserInteraction
        fields = ["product", "interaction_type", "session_key", "metadata"]

    def validate_interaction_type(self, value):
        if value not in self.ALLOWED_TYPES:
            raise serializers.ValidationError(
                f"Frontend may only log: {', '.join(self.ALLOWED_TYPES)}"
            )
        return value

    def validate(self, attrs):
        from interactions.models import INTERACTION_WEIGHTS

        attrs["weight"] = INTERACTION_WEIGHTS.get(attrs["interaction_type"], 1.0)
        return attrs


class UserInteractionHistorySerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source="product.title", read_only=True)
    product_id = serializers.UUIDField(source="product.product_id", read_only=True)

    class Meta:
        model = UserInteraction
        fields = [
            "id",
            "interaction_type",
            "product_id",
            "product_title",
            "weight",
            "metadata",
            "created_at",
        ]
