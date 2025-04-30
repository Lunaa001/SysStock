from django.shortcuts import render

# Create your views here.
##from rest_framework import viewsets
##from .serializer import *
##from .models import 

from rest_framework import viewsets
from .models import Branch, Product, Provider  # Importa solo los modelos necesarios
from AccountAdmin.models import User  # Importa User desde AccountAdmin
from .serializer import BranchSerializer, ProductSerializer, ProviderSerializer, UserSerializer
from AccountAdmin.permissions import IsAdminUser

from rest_framework.permissions import BasePermission

class CanAddProduct(BasePermission):
    """
    Permiso que permite agregar productos a usuarios con rol 'admin' o 'limMerchant'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.rol == 'admin' or request.user.rol == 'limMerchant'
        )

class CanManageProduct(BasePermission):
    """
    Permiso que permite agregar, borrar o modificar productos a usuarios con rol 'admin' o 'limMerchant'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.rol == 'admin' or request.user.rol == 'limMerchant'
        )
    
class CanDeleteProduct(BasePermission):
    """
    Permiso que permite borrar productos a usuarios con rol 'admin' o 'limMerchant'.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.rol == 'admin' or request.user.rol == 'limMerchant'
        )



class BranchView(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    queryset = Branch.objects.all()
   
    def get_queryset(self):
        # Si el usuario es admin, puede ver todas las sucursales
        if self.request.user.rol == 'admin':
            return Branch.objects.all()
        # Si el usuario es limitado, solo puede ver su sucursal
        return Branch.objects.filter(id=self.request.user.sucursal)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:  # Crear, editar o borrar sucursales
            self.permission_classes = [IsAdminUser]  # Solo los administradores pueden realizar estas acciones
        elif self.action == 'list':  # Listar sucursales
            self.permission_classes = [IsAdminUser]  # Solo los administradores pueden listar sucursales
        return super().get_permissions()

    

class  ProductView(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    
    def get_queryset(self):
        # Si el usuario es admin, puede ver todos los productos
        if self.request.user.rol == 'admin':
            return Product.objects.all()
        # Si el usuario es limitado, solo puede ver productos de su sucursal
        return Product.objects.filter(sucursal=self.request.user.sucursal)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:  # Crear, editar o borrar productos
            self.permission_classes = [CanManageProduct]
        elif self.action == 'list':  # Listar productos
            self.permission_classes = [CanManageProduct]  # Tanto admin como limMerchant pueden listar productos
        return super().get_permissions()


class ProviderView(viewsets.ModelViewSet):
    serializer_class = ProviderSerializer
    queryset = Provider.objects.all()
    
    def get_queryset(self):
        # Si el usuario es admin, puede ver todos los proveedores
        if self.request.user.rol == 'admin':
            return Provider.objects.all()
        # Si el usuario es limitado, solo puede ver proveedores relacionados con su sucursal
        return Provider.objects.filter(product__sucursal=self.request.user.sucursal).distinct()

    permission_classes = [IsAdminUser]  # Solo los administradores pueden acceder