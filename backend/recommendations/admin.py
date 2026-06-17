from django.contrib import admin
from interactions.models import ProductPopularityScore, SearchQuery, UserInteraction


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "actor",
        "interaction_type",
        "product_title",
        "weight",
        "created_at",
    ]
    list_filter = ["interaction_type", "created_at"]
    search_fields = ["user__email", "session_key", "product__title"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def actor(self, obj):
        return obj.user.email if obj.user else f"anon:{obj.session_key[:8]}"

    actor.short_description = "Actor"

    def product_title(self, obj):
        return obj.product.title if obj.product else "—"

    product_title.short_description = "Product"


@admin.register(ProductPopularityScore)
class ProductPopularityScoreAdmin(admin.ModelAdmin):
    list_display = [
        "product",
        "score",
        "view_count",
        "purchase_count",
        "cart_add_count",
        "last_computed_at",
    ]
    ordering = ["-score"]
    readonly_fields = ["last_computed_at"]


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ["query_text", "source", "results_count", "user", "created_at"]
    list_filter = ["source", "created_at"]
    search_fields = ["query_text"]
    ordering = ["-created_at"]
