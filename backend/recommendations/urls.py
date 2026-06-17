from django.urls import path

from recommendations.views import (
    ForYouView,
    MLModelRegistryView,
    SimilarItemsView,
    TrendingView,
    VisualSearchView,
)

app_name = "recommendations"

urlpatterns = [
    path("for-you/", ForYouView.as_view(), name="for-you"),
    path(
        "similar/<uuid:product_id>/", SimilarItemsView.as_view(), name="similar-items"
    ),
    path("trending/", TrendingView.as_view(), name="trending"),
    path("visual-search/", VisualSearchView.as_view(), name="visual-search"),
    path("models/", MLModelRegistryView.as_view(), name="model-registry"),
]
