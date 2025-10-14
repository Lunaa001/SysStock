# AccountAdmin/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .views import RegisterView, LogoutView, AdminUserCreateView

from django.urls import path
from .views import RegisterView, LoginView, LogoutView, AdminUserCreateView, CSRFTokenView

urlpatterns = [
    # Auth pública (JSON)
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/",    LoginView.as_view(),    name="login"),
    path("auth/logout/",   LogoutView.as_view(),   name="logout"),

    # CSRF helper (por si usás fetch/axios/Postman)
    path("csrf/", CSRFTokenView.as_view(), name="csrf"),

    # Solo admin
    path("admin/users/create/", AdminUserCreateView.as_view(), name="admin_user_create"),
]
