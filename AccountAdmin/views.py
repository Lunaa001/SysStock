from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import ReassignBranchSerializer

from .serializers import WorkerSerializer 

from .serializers import RegisterSerializer, AdminCreateUserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "rol": user.rol,
            "sucursal_id": user.sucursal_id,
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_201_CREATED)


class AdminUserCreateView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminCreateUserSerializer

    def post(self, request, *args, **kwargs):
        if request.user.rol != "admin":
            return Response({"detail": "Solo el admin puede crear empleados."}, status=403)

        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "rol": user.rol,
            "sucursal_id": user.sucursal_id,
        }, status=status.HTTP_201_CREATED)

class AdminUserReassignBranchView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReassignBranchSerializer

    def post(self, request, *args, **kwargs):
        # Solo admin
        if getattr(request.user, "rol", None) != "admin":
            return Response({"detail": "Solo el admin puede reasignar usuarios."}, status=403)

        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        u = ser.save()
        return Response({
            "id": u.id,
            "username": u.username,
            "rol": u.rol,
            "sucursal_id": u.sucursal_id
        }, status=status.HTTP_200_OK)

User = get_user_model()

class AdminWorkersListView(GenericAPIView):
    """
    GET /api/admin/users/?sucursal_id=<id>
    - Lista todos los empleados (rol=limMerchant) del admin autenticado.
    - Si pasás sucursal_id, filtra solo esa sucursal.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = WorkerSerializer

    def get(self, request, *args, **kwargs):
        if getattr(request.user, "rol", None) != "admin":
            return Response({"detail": "Solo admin."}, status=403)

        qs = User.objects.filter(rol="limMerchant", sucursal__owner=request.user)

        sucursal_id = request.query_params.get("sucursal_id")
        if sucursal_id:
            qs = qs.filter(sucursal_id=sucursal_id)

        ser = self.get_serializer(qs.order_by("id"), many=True)
        return Response(ser.data, status=200)


class AdminUserDeleteView(GenericAPIView):
    """
    DELETE /api/admin/users/<user_id>/
    - Borra un empleado (rol=limMerchant) que pertenezca a alguna sucursal del admin.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id, *args, **kwargs):
        if getattr(request.user, "rol", None) != "admin":
            return Response({"detail": "Solo admin."}, status=403)

        try:
            u = User.objects.get(
                id=user_id,
                rol="limMerchant",
                sucursal__owner=request.user
            )
        except User.DoesNotExist:
            return Response({"detail": "Usuario no encontrado o no te pertenece."}, status=404)

        u.delete()
        return Response(status=204)