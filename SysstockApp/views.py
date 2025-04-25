from django.shortcuts import render

# Create your views here.
##from rest_framework import viewsets
##from .serializer import *
##from .models import 

from rest_framework import viewsets
from .models import Branch, Product, Provider  # Importa solo los modelos necesarios
from AccountAdmin.models import User  # Importa User desde AccountAdmin
from .serializer import BranchSerializer, ProductSerializer, ProviderSerializer, UserSerializer
from AccountAdmin.permissions import IsAdminUser



class BranchView(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    queryset = Branch.objects.all()

class UserView(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    

class  ProductView(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()


class ProviderView(viewsets.ModelViewSet):
    serializer_class = ProviderSerializer
    queryset = Provider.objects.all()

