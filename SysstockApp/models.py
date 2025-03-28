from django.db import models

class Sucursal(models.Model):
    name=models.TextField(max_length=100)

# Modelo de Usuario (hereda de AbstractUser para personalización)

class Usuario(models.Model):

    ROLES = [
        ('admin', 'Administrador'),
        ('limMerchant', 'Limitado'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    email= models.EmailField(unique=True)

# Modelo de Proveedor

class Proveedor(models.Model):
    nombre = models.CharField(max_length=255)
    contacto = models.CharField(max_length=100)
    direccion = models.TextField()


# Modelo de Producto

class Producto(models.Model):
    nombre = models.CharField(max_length=255)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.IntegerField()
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)


# Create your models here.
