from django.db import models
from django.contrib.auth.models import AbstractUser
from SysstockApp.models import Branch
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ADMIN = "admin"
    LIMMERCHANT = "limMerchant"

    ROLE_CHOICES = [
        (ADMIN, "Administrador"),
        (LIMMERCHANT, "Limmerchant")
    ]

    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ADMIN)

    company_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    sucursal = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="usuarios"
    )

    def clean(self):
        if self.rol == self.LIMMERCHANT and self.sucursal is None:
            raise ValidationError("Un empleado limMerchant debe tener una sucursal asignada.")

    def __str__(self):
        return f"{self.username} ({self.rol})"
