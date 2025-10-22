# AccountAdmin/views.py
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, AdminCreateUserSerializer

class RegisterView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()  # crea usuario con sucursal asignada + admin por defecto

        # devuelve tokens para que el cliente pueda loguearse directo si quiere
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "rol": user.rol,
                "sucursal_id": user.sucursal_id,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )

class AdminUserCreateView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminCreateUserSerializer

    def post(self, request, *args, **kwargs):
        # Solo admins pueden crear usuarios
        if getattr(request.user, "rol", None) != "admin":
            return Response({"detail": "Solo admins"}, status=status.HTTP_403_FORBIDDEN)

        ser = self.get_serializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        u = ser.save()
        return Response(
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "rol": u.rol,
                "sucursal_id": u.sucursal_id,
            },
            status=status.HTTP_201_CREATED,
        )
