from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class IsAuthenticatedCustom(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            # if not request.user.is_active:
                # return True
            raise PermissionDenied("Access denied: This account is not active")
        raise PermissionDenied("Authetication required")


class IsAdminUserCustom(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            # if not request.user.is_active:
            if request.user.is_staff or request.user.is_superuser:
                return True
            raise PermissionDenied("Access denied: Admin privileges required!")
            # raise PermissionDenied("Access denied: This account is not active")
        raise PermissionDenied("Authentication required!")


class ApiAuthMixin:
    permission_classes = (IsAuthenticatedCustom, )

class AdminApiAuthMixin:
    permission_classes = (IsAdminUserCustom,)