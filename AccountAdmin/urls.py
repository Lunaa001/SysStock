# AccountAdmin/urls.py
from django.urls import path
from .views import RegisterView, AdminUserCreateView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("admin/users/create/", AdminUserCreateView.as_view(), name="admin_user_create"),
]
