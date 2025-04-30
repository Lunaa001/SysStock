from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLES = [
        ('admin', 'Administrador'),
        ('limMerchant', 'Limitado'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES, default='limMerchant')
    sucursal = models.CharField(max_length=100, default='', blank=True)  # Cambiado a CharField para almacenar el nombre de la sucursal

    def __str__(self):
        return self.email
# Create your models here.
