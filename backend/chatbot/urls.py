from django.urls import path

from chatbot.views import ChatSessionDetailView, ChatSessionListView, ChatView

app_name = "chatbot"

urlpatterns = [
    path("chat/",                     ChatView.as_view(),             name="chat"),
    path("sessions/",                 ChatSessionListView.as_view(),  name="session-list"),
    path("sessions/<uuid:session_id>/", ChatSessionDetailView.as_view(), name="session-detail"),
]
