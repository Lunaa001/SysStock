from django.db import models
from django.conf import settings

class Category(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    def __str__(self): return self.nombre

class Branch(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, null=True, blank=True)
    
    # DUEÑO de la sucursal (ADMIN de esa empresa)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sucursales",
        null=True,      # temporalmente null para no romper migraciones
        blank=True
    )

    class Meta:
        ordering = ["id"]
        unique_together = ("owner", "name")  # un nombre por empresa

    def __str__(self):
        return f"{self.name} ({self.owner})"

class Product(models.Model):
    nombre = models.CharField(max_length=255)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    categoria = models.ForeignKey(
    Category,
    on_delete=models.PROTECT,
    related_name='productos',
    null=True,
    blank=True,
    )
    sucursal = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='productos')

    def __str__(self): return f"{self.nombre} ({self.categoria.nombre})"

    @property
    def cantidad(self):
        agg = self.movimientos.aggregate(total=models.Sum('cantidad_signed'))
        return agg['total'] or 0

class StockMovement(models.Model):
    IN = 'IN'; OUT = 'OUT'
    TYPES = [(IN,'Ingreso'), (OUT,'Egreso')]
    producto = models.ForeignKey(Product, related_name='movimientos', on_delete=models.CASCADE)
    sucursal = models.ForeignKey(Branch, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=3, choices=TYPES)
    cantidad = models.PositiveIntegerField()
    cantidad_signed = models.IntegerField(editable=False)
    motivo = models.CharField(max_length=255, blank=True, null=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        self.cantidad_signed = self.cantidad if self.tipo == self.IN else -int(self.cantidad)
        super().save(*args, **kwargs)

class Sale(models.Model):
    sucursal = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='ventas')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    @property
    def total(self):
        agg = self.items.aggregate(
            s=models.Sum(models.F('cantidad') * models.F('precio_unit'),
                         output_field=models.DecimalField(max_digits=14, decimal_places=2))
        )
        return agg['s'] or 0

class SaleItem(models.Model):
    venta = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Product, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unit = models.DecimalField(max_digits=12, decimal_places=2)
    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(cantidad__gte=1), name="saleitem_cantidad_gte_1")
        ]
