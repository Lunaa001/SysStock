from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLES = [
        ('admin', 'Administrador'),
        ('limMerchant', 'Limitado'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES, default='limMerchant')
    # nombre de sucursal en texto (simple). Si querés FK a Branch, avisá y lo cambio.
    sucursal = models.CharField(max_length=100, default='', blank=True, null=True)

    def __str__(self):
        return self.username or self.email or f"User {self.pk}"
