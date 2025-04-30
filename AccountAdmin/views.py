from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import IsAuthenticated
from AccountAdmin.serializer import UserSerializer


from rest_framework import viewsets
from .serializer import *
from .models import *

from AccountAdmin.permissions import IsAdminUser, CanListUsers


class UserView(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]  # Solo los administradores pueden acceder
    queryset = User.objects.all()  

    def get_permissions(self):
        if self.action == 'list':  # Restringir la acción de listar usuarios
            self.permission_classes = [CanListUsers]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:  # Crear, editar o borrar usuarios
            self.permission_classes = [IsAdminUser]  # Solo administradores pueden realizar estas acciones
        return super().get_permissions()

class LoginView(APIView):
    def post(self, request):
        
        username = request.data.get("username")
        password = request.data.get("password")
        print(username, password)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({
                "message": "Login exitoso",
                "username": user.username,
                "rol": user.rol,
                "email": user.email,
                "password": user.password,
                
            }, status=status.HTTP_200_OK)
        return Response({"error": "Credenciales inválidas"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logout exitoso"}, status=status.HTTP_200_OK)

