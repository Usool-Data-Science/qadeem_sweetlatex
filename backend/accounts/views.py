from core.utils import merge_carts
from django.conf import settings
from djoser.social.views import ProviderAuthView
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .serializers import CustomTokenObtainPairSerializer


class CustomProviderAuthView(ProviderAuthView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 201:
            # Social Auth views usually return the user in the serializer context
            # or you can fetch them via the access token

            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")

            response.set_cookie(
                "access",
                access_token,
                # domain=settings.AUTH_COOKIE_DOMAIN,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )
            response.set_cookie(
                "refresh",
                refresh_token,
                # domain=settings.AUTH_COOKIE_DOMAIN,
                max_age=settings.AUTH_COOKIE_MAX_AGE,
                path=settings.AUTH_COOKIE_PATH,
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
            )

            # Extract user from the newly created token
            try:
                token = AccessToken(access_token)
                user_id = token["user_id"]
                from django.contrib.auth import get_user_model

                user = get_user_model().objects.get(id=user_id)

                session_id = request.headers.get("X-Session-ID") or request.COOKIES.get(
                    "sessionid"
                )
                if session_id:
                    from core.utils import merge_carts

                    merge_carts(user, session_id)
            except Exception:
                pass

        return response


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        # We need the serializer to get the user object
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # The user object is available in validated_data after serializer runs
        user = serializer.user
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            self._set_auth_cookies(response)

            # Merge carts if session_id exists
            session_id = request.headers.get("X-Session-ID") or request.COOKIES.get(
                "session_id"
            )
            if session_id and user:
                merge_carts(user, session_id)
        return response

    def _set_auth_cookies(self, response):
        access_token = response.data.get("access")
        refresh_token = response.data.get("refresh")

        response.set_cookie(
            "access",
            access_token,
            # domain=settings.AUTH_COOKIE_DOMAIN,
            max_age=settings.AUTH_COOKIE_MAX_AGE,
            path=settings.AUTH_COOKIE_PATH,
            secure=settings.AUTH_COOKIE_SECURE,
            httponly=settings.AUTH_COOKIE_HTTP_ONLY,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )

        response.set_cookie(
            "refresh",
            refresh_token,
            # domain=settings.AUTH_COOKIE_DOMAIN,
            max_age=settings.AUTH_COOKIE_MAX_AGE,
            path=settings.AUTH_COOKIE_PATH,
            secure=settings.AUTH_COOKIE_SECURE,
            httponly=settings.AUTH_COOKIE_HTTP_ONLY,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )

        response.data.__delitem__("access")
        response.data.__delitem__("refresh")


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        refresh_token = request.COOKIES.get("refresh")

        if refresh_token:
            # request.data['refresh'] = refresh_token # This might throw error if it is immutable
            data = request.data.copy()
            data["refresh"] = refresh_token
            request._full_data = data

            response = super().post(request, *args, **kwargs)

            if response.status_code == 200:
                access_token = response.data.get("access")
                refresh_token = response.data.get(
                    "refresh"
                )  # In case of refresh token rotation

                response.set_cookie(
                    "access",
                    access_token,
                    # domain=settings.AUTH_COOKIE_DOMAIN,
                    max_age=settings.AUTH_COOKIE_MAX_AGE,
                    path=settings.AUTH_COOKIE_PATH,
                    secure=settings.AUTH_COOKIE_SECURE,
                    httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                    samesite=settings.AUTH_COOKIE_SAMESITE,
                )
                if refresh_token:
                    response.set_cookie(
                        "refresh",
                        refresh_token,
                        # domain=settings.AUTH_COOKIE_DOMAIN,
                        max_age=settings.AUTH_COOKIE_MAX_AGE,
                        path=settings.AUTH_COOKIE_PATH,
                        secure=settings.AUTH_COOKIE_SECURE,
                        httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                        samesite=settings.AUTH_COOKIE_SAMESITE,
                    )
                # Ensure to clear response only after success, otherwise you will clear off 401 error.
                response.data = {}

            return response
        else:
            return Response({"detail": "Refresh token missing"}, status=400)


class CustomTokenVerifyView(TokenVerifyView):
    def post(self, request, *args, **kwargs):
        access_token = request.COOKIES.get("access")
        if access_token:
            # request.data['token'] = access_token
            data = request.data.copy()
            data["token"] = access_token
            request._full_data = data

            return super().post(request, *args, **kwargs)
        else:
            return Response({"detail": "Access token missing"}, status=400)


class LogoutView(APIView):
    def post(self, request, *args, **kwargs):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(
            "access",
            path=settings.AUTH_COOKIE_PATH,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )

        response.delete_cookie(
            "refresh",
            # domain=settings.AUTH_COOKIE_DOMAIN,
            path=settings.AUTH_COOKIE_PATH,
            samesite=settings.AUTH_COOKIE_SAMESITE,
        )

        refresh_token = request.COOKIES.get("refresh")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass  # token already invalid / malformed

        return response
