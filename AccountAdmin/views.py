from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView


from .permissions import IsAdminRole
from .serializers import (
    RegisterSerializer,
    AdminUserReadSerializer,
    AdminCreateUserSerializer,
    ChangeUserBranchSerializer,
)

User = get_user_model()


# --------- REGISTER PÚBLICO ----------
class RegisterView(CreateAPIView):
    """
    POST /api/auth/register/
    Body:
    {
      "username": "",
      "email": "",
      "password": "",
      "password2": "",
      "company": { "name": "", "phone": "", "address": "" }
    }
    """
    serializer_class = RegisterSerializer
    authentication_classes = []
    permission_classes = [AllowAny]


# --------- CREAR EMPLEADO (limMerchant) POR ADMIN ----------
class AdminUserCreateView(CreateAPIView):
    """
    POST /api/admin/users/create/
    """
    serializer_class = AdminCreateUserSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    # ✅ Responde con el serializer de lectura (rol, sucursal, etc.)
    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        user = ser.save()
        read = AdminUserReadSerializer(user)
        return Response(read.data, status=status.HTTP_201_CREATED)


# --------- LISTAR / DETALLE / BORRAR / TRANSFERIR ----------
class AdminUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    """
    - GET    /api/admin/users/            -> listar (solo tus usuarios, sin mostrarte a vos)
    - GET    /api/admin/users/{id}/       -> detalle
    - DELETE /api/admin/users/{id}/       -> borrar
    - PATCH  /api/admin/users/{id}/change-branch/ -> cambiar sucursal
    """
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get_queryset(self):
        user = self.request.user
        UserModel = get_user_model()

        if getattr(user, "is_superuser", False):
            return UserModel.objects.all().order_by("id")

        # Solo yo y empleados de mis sucursales
        return UserModel.objects.filter(
            Q(id=user.id) | Q(sucursal__owner=user)
        ).order_by("id")

    def get_serializer_class(self):
        return AdminUserReadSerializer

    # ✅ Opción A — no mostrar al admin logueado en el listado
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        if not request.user.is_superuser:
            qs = qs.exclude(id=request.user.id)  # ocultar admin actual
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)

    @action(detail=True, methods=["patch"], url_path="change-branch")
    def change_branch(self, request, pk=None):
        user_to_move = self.get_object()

        # 🚫 no mover admins (salvo superuser)
        if getattr(user_to_move, "rol", None) == "admin" and not getattr(request.user, "is_superuser", False):
            return Response({"detail": "No puedes transferir la sucursal de un admin."},
                            status=status.HTTP_403_FORBIDDEN)

        ser = ChangeUserBranchSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        target_branch = ser.validated_data["_branch_obj"]

        # 🚫 no adopciones entre empresas (empleado ya asignado a sucursal de otro admin)
        if not getattr(request.user, "is_superuser", False):
            current_branch = getattr(user_to_move, "sucursal", None)
            if current_branch and getattr(current_branch, "owner_id", None) != request.user.id:
                return Response({"detail": "No puedes trasladar empleados que pertenecen a otra empresa."},
                                status=status.HTTP_403_FORBIDDEN)

        if not hasattr(user_to_move, "sucursal"):
            return Response({"detail": "El modelo User no tiene FK 'sucursal'."}, status=400)

        user_to_move.sucursal = target_branch
        user_to_move.save(update_fields=["sucursal"])
        return Response(AdminUserReadSerializer(user_to_move).data, status=200)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": "Usuario eliminado con éxito"}, status=status.HTTP_200_OK)

class MeView(APIView):
    """
    GET /api/me/

    Devuelve info básica del usuario logueado:
    - id, username, email
    - rol (admin / limMerchant)
    - sucursal {id, name} si tiene
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "rol": getattr(user, "rol", None),
            "is_superuser": user.is_superuser,
            "sucursal": None,
        }

        branch = getattr(user, "sucursal", None)
        if branch:
            data["sucursal"] = {
                "id": branch.id,
                "name": getattr(branch, "name", None),
            }

        return Response(data, status=200)