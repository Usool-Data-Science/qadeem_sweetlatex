from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            raw_token = request.COOKIES.get(settings.AUTH_COOKIE)
        else:
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except (InvalidToken, TokenError):
            # Token is expired or invalid.
            # Return None so Django treats this as an anonymous request.
            # Public endpoints (AllowAny) will continue serving normally.
            # Protected endpoints will return 401 via DRF's permission check,
            # which then triggers the RTK Query refresh flow in the frontend.
            return None

        return self.get_user(validated_token), validated_token
