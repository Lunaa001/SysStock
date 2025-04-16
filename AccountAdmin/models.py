from django.db import models
from SysstockApp.models import Branch

class User(models.Model):

    ROLES = [
        ('admin', 'Administrador'),
        ('limMerchant', 'Limitado'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES)
    sucursal = models.ForeignKey(Branch, on_delete=models.CASCADE)
    email= models.EmailField(unique=True)


    def __str__(self):
        return self.name
# Create your models here.
