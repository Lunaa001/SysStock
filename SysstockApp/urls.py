from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    CategoryViewSet, BranchViewSet, ProductViewSet,
    StockMovementViewSet, SaleViewSet,
    low_stock, export_sales_excel
)

router = DefaultRouter()
router.register(r"categorias", CategoryViewSet, basename="categorias")
router.register(r"sucursales", BranchViewSet, basename="sucursales")
router.register(r"productos", ProductViewSet, basename="productos")
router.register(r"movimientos", StockMovementViewSet, basename="movimientos")
router.register(r"ventas", SaleViewSet, basename="ventas")

urlpatterns = [
    path("", include(router.urls)),
    path("stock/low/", low_stock),                    # GET ?threshold=5
    path("ventas/export/xlsx/", export_sales_excel),  # solo admin
]
