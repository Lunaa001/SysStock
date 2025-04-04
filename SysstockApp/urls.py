from django.urls import path, include
from rest_framework import routers
from . import views  # Importa las vistas de tu aplicación

# Define el router y registra las vistas
router = routers.DefaultRouter()
router.register(r'sucursales', views.SucursalView, basename='Sucursal')


# Define las rutas
urlpatterns = [
    path('SisstockApp/', include(router.urls)),  # Prefijo para las rutas de la API
]