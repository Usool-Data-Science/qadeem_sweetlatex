from django.urls import path, re_path
from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    CustomProviderAuthView,
    LogoutView)

urlpatterns = [
    re_path(r'^o/(?P<provider>\S+)/$', CustomProviderAuthView.as_view(), name='provider-auth'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login_user'),
    path('refresh/', CustomTokenRefreshView.as_view(), name='refresh_user'),
    path('verify/', CustomTokenVerifyView.as_view(), name='verify_user'),
    path('logout/', LogoutView.as_view(), name='logout_user'),
]