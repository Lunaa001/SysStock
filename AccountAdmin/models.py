from django.db import models
from django.contrib.auth.models import AbstractUser
from SysstockApp.models import Branch

class User(AbstractUser):
    ADMIN = "admin"
    LIMMERCHANT = "limMerchant"
    ROLE_CHOICES = [(ADMIN, "Administrador"), (LIMMERCHANT, "Limmerchant")]

    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, default=LIMMERCHANT)
    email = models.EmailField(unique=True)
    sucursal = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="usuarios")

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return f"{self.username} ({self.rol})"
