from django.db import models


class Branch(models.Model):
    name=models.CharField(max_length=100)
 
    def __str__(self):
        return self.name

# Modelo de Proveedor

class Provider(models.Model):
    nombre = models.CharField(max_length=255)
    contacto = models.CharField(max_length=100)
    direccion = models.TextField()


# Modelo de Producto

class Product(models.Model):
    nombre = models.CharField(max_length=255)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.IntegerField()
    proveedor = models.ForeignKey(Provider, on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Branch, on_delete=models.CASCADE)


# Create your models here.
