from django.urls import path

from interactions.views import (
    InteractionHistoryView,
    LogInteractionView,
    StitchSessionView,
)

app_name = "interactions"

urlpatterns = [
    path("log/", LogInteractionView.as_view(), name="log"),
    path("history/", InteractionHistoryView.as_view(), name="history"),
    path("stitch/", StitchSessionView.as_view(), name="stitch"),
]
