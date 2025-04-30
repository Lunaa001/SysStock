from rest_framework.permissions import BasePermission


class CanListUsers(BasePermission):
    """
    Permiso que permite listar usuarios solo a los administradores.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'admin'

class IsAdminUser(BasePermission):
    """
    Permiso que permite el acceso solo a usuarios con rol 'admin'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'admin'


class IsLimitedUser(BasePermission):
    """
    Permiso que permite el acceso solo a usuarios con rol 'limMerchant'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'limMerchant'
    

class CanAddProduct(BasePermission):
    """
    Permiso que permite agregar productos solo a los administradores.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'admin'
    
from rest_framework.permissions import BasePermission

class CanManageProduct(BasePermission):
    """
    Permiso que permite gestionar productos solo a los administradores.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'admin'