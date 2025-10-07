# AccountAdmin/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

# OJO: si tu archivo es serializers.py (plural), cambiá a .serializers
from .serializer import PublicRegisterSerializer, AdminCreateUserSerializer
from .permissions import IsAdmin

User = get_user_model()


# Registro público: SOLO email + password (username=email, rol=limMerchant)
class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicRegisterSerializer

    # Devuelve tokens y datos básicos del usuario recién creado
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # crea username=email, rol=limMerchant

        refresh = RefreshToken.for_user(user)
        data = {
            "username": user.username,
            "email": user.email,
            "rol": getattr(user, "rol", None),
            "sucursal": getattr(user, "sucursal", ""),
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


# Logout (en JWT es client-side: el cliente descarta el token)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Si en el futuro usás blacklist, acá podrías “blacklistear” el refresh.
        return Response({"message": "Logout ok (borra el token en el cliente)"}, status=status.HTTP_200_OK)


# Crear usuario (solo admin): username + email + password (+ rol + sucursal opcional)
class AdminUserCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminCreateUserSerializer
