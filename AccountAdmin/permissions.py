from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "rol", None) == "admin"

class IsLimitedMerchant(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "rol", None) == "limMerchant"
