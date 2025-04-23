from django.urls import path, include
from rest_framework import routers
from . import views  # Importa las vistas de tu aplicación

# Define el router y registra las vistas
router = routers.DefaultRouter()
router.register(r'Branch', views.BranchView, basename='Sucursal')
router.register(r'Product', views.ProductView, basename='Producto')
router.register(r'Provider', views.ProviderView, basename='Provedor')
router.register(r'User', views.UserView, basename='Usuario')

# Define las rutas
urlpatterns = [
    path('SisstockApp/', include(router.urls)),  # Prefijo para las rutas de la API  
]
