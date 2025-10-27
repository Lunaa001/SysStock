from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    """
    Permite solo usuarios autenticados con rol == 'admin'
    """
    message = "Se requiere rol admin."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and getattr(user, "rol", None) == "admin")

# Alias por compatibilidad con imports existentes (p.ej. IsAdmin)
IsAdmin = IsAdminRole
IsAdminUser = IsAdminRole

__all__ = ["IsAdminRole", "IsAdmin", "IsAdminUser"]
