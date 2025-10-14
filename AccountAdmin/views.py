# AccountAdmin/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.middleware.csrf import get_token

# OJO: si tu archivo es serializers.py (plural), cambia a .serializers
from .serializer import PublicRegisterSerializer, AdminCreateUserSerializer
from .permissions import IsAdmin

User = get_user_model()


# --- Registro público: SOLO email + password (username=email, rol=limMerchant)
class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicRegisterSerializer
    # devuelve 201 con los datos del serializer; NO devuelve tokens


# --- Login con cookies de sesión (requiere CSRF)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({"detail": "Credenciales inválidas"}, status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)  # setea cookie de sesión
        return Response({
            "message": "Login ok",
            "username": user.username,
            "rol": getattr(user, "rol", None),
            "sucursal": getattr(user, "sucursal", ""),
        }, status=status.HTTP_200_OK)


# --- Logout con cookies (requiere CSRF y estar autenticado)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logout ok"}, status=status.HTTP_200_OK)


# --- Crear usuario (solo admin)
class AdminUserCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AdminCreateUserSerializer


# --- CSRF helper: setea cookie csrftoken y devuelve el token
class CSRFTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = get_token(request)
        return Response({"csrfToken": token}, status=status.HTTP_200_OK)
