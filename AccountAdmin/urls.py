# AccountAdmin/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .views import RegisterView, LogoutView, AdminUserCreateView

urlpatterns = [
    # Auth pública
    path("auth/register/", RegisterView.as_view(), name="register"),

    # JWT: login / refresh / verify
    path("auth/login/",   TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(),    name="token_refresh"),
    path("auth/verify/",  TokenVerifyView.as_view(),     name="token_verify"),

    # Logout (client-side)
    path("auth/logout/",  LogoutView.as_view(), name="logout"),

    # Solo admin
    path("admin/users/create/", AdminUserCreateView.as_view(), name="admin_user_create"),
]
