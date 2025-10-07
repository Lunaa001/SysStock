from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, BranchViewSet, ProductViewSet,
    StockMovementViewSet, SaleViewSet
)

router = DefaultRouter()
router.register(r"categorias", CategoryViewSet, basename="categorias")
router.register(r"sucursales", BranchViewSet, basename="sucursales")
router.register(r"productos", ProductViewSet, basename="productos")
router.register(r"movimientos", StockMovementViewSet, basename="movimientos")
router.register(r"ventas", SaleViewSet, basename="ventas")

urlpatterns = router.urls
