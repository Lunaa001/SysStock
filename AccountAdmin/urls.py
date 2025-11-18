from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenBlacklistView

from .views import (
    RegisterView,
    AdminUserCreateView,
    AdminUserViewSet,
    MeView,   # 👈 CORRECTO
)

router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-users')

urlpatterns = [
    # Register público
    path("auth/register/", RegisterView.as_view(), name="auth-register"),

    # Crear empleado (limMerchant)
    path("admin/users/create/", AdminUserCreateView.as_view(), name="admin_user_create"),

    # Logout con Blacklist
    path("auth/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),

    # Endpoints del router (listar / detalle / delete / change-branch)
    path("", include(router.urls)),

    # Perfil del usuario logueado (me)
    path("me/", MeView.as_view(), name="me"),  # 👈 CORRECTO
]
