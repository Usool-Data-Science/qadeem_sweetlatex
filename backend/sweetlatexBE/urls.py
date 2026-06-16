from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("common.urls")),
    path("sweet-administration/", admin.site.urls),
    path("api/", include("djoser.urls")),
    path("api/", include("accounts.urls")),
    path("api/", include("core.urls")),
]
