from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    CategoryViewSet, BranchViewSet, ProductViewSet,
    StockMovementViewSet, SaleViewSet,
    low_stock, export_sales_excel,
    ventas_hoy_empresa,
    kardex_producto, kardex_producto_xlsx,
)

router = DefaultRouter()
router.register(r"categorias", CategoryViewSet, basename="categorias")
router.register(r"sucursales", BranchViewSet, basename="sucursales")
router.register(r"productos", ProductViewSet, basename="productos")
router.register(r"movimientos", StockMovementViewSet, basename="movimientos")
router.register(r"ventas", SaleViewSet, basename="ventas")

urlpatterns = [
    path("", include(router.urls)),

    # Bajo stock (usa stock_min o threshold global)
    path("stock/low/", low_stock, name="stock-low"),

    # Exportar ventas globales (solo admin)
    path("ventas/export/xlsx/", export_sales_excel, name="ventas-export-xlsx"),

    # Ventas del día por empresa (JSON)
    path("ventas/hoy/empresa", ventas_hoy_empresa, name="ventas-hoy-empresa"),

    # Kardex por producto (JSON + Excel)
    path("productos/<int:producto_id>/kardex", kardex_producto, name="kardex-producto"),
    path("productos/<int:producto_id>/kardex/xlsx", kardex_producto_xlsx, name="kardex-producto-xlsx"),
]
