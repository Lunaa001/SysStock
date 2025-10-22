from django.urls import path
from .views import RegisterView, AdminUserCreateView, AdminUserReassignBranchView
from rest_framework_simplejwt.views import TokenBlacklistView
from .views import (
    RegisterView, AdminUserCreateView, AdminUserReassignBranchView,
    AdminWorkersListView, AdminUserDeleteView
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("admin/users/create/", AdminUserCreateView.as_view(), name="admin_user_create"),
    path("admin/users/reassign-branch/", AdminUserReassignBranchView.as_view(), name="admin_user_reassign_branch"),
    path("admin/users/", AdminWorkersListView.as_view(), name="admin_user_list"),
    path("admin/users/<int:user_id>/", AdminUserDeleteView.as_view(), name="admin_user_delete"),
    path("auth/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
]