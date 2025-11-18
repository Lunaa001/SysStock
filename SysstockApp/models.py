from django.conf import settings
from django.db import models
from django.db.models import F, Q, Sum, DecimalField


# =========================
#  Categorías
# =========================
class Category(models.Model):
    nombre = models.CharField(max_length=100, unique=False)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    # Dueño (el admin / empresa). Null=True para migraciones sin romper.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categorias",
        null=True,
        blank=True,
    )

    class Meta:
        # Evita duplicados por empresa (owner + nombre)
        unique_together = ("owner", "nombre")
        ordering = ["id"]

    def __str__(self):
        return self.nombre

# =========================
#  Sucursales
# =========================
class Branch(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, null=True, blank=True)
    telefono = models.CharField(max_length=30, null=True, blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sucursales",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["id"]
        unique_together = ("owner", "name")

    def __str__(self):
        return f"{self.name} ({self.owner})"


# =========================
#  Productos
# =========================
class Product(models.Model):
    nombre = models.CharField(max_length=255)
    precio = models.DecimalField(max_digits=12, decimal_places=2)

    categoria = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="productos",
        null=True,
        blank=True,
    )
    sucursal = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="productos")

    # NUEVOS (opcionales)
    sku = models.CharField(max_length=64, null=True, blank=True)
    stock_min = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["nombre"]),
            models.Index(fields=["sucursal"]),
            models.Index(fields=["categoria"]),
        ]

    def __str__(self):
        cat = self.categoria.nombre if self.categoria else "Sin categoría"
        return f"{self.nombre} ({cat})"

    @property
    def cantidad(self):
        """
        Stock actual vía suma de 'cantidad_signed' de sus movimientos.
        """
        agg = self.movimientos.aggregate(total=models.Sum("cantidad_signed"))
        return agg["total"] or 0


# =========================
#  Movimientos de stock

class StockMovement(models.Model):
    IN = "IN"
    OUT = "OUT"
    SALE = "SALE"

    TYPES = [
        (IN, "Ingreso"),
        (OUT, "Egreso"),
        (SALE, "Venta"),
    ]

    producto = models.ForeignKey(
        "Product",
        related_name="movimientos",
        on_delete=models.CASCADE
    )
    sucursal = models.ForeignKey("Branch", on_delete=models.PROTECT)

    # 👉 Aumentamos max_length porque ahora podemos guardar "SALE"
    tipo = models.CharField(max_length=8, choices=TYPES)

    cantidad = models.PositiveIntegerField()  # entero positivo
    # campo firmado para agilizar SUM (IN=+cantidad, OUT/SALE=-cantidad)
    cantidad_signed = models.IntegerField(editable=False)

    # opcional: motivo/memo del movimiento
    motivo = models.CharField(max_length=255, blank=True, null=True)

    # opcional: costo unitario (no impacta stock; útil para valorización a futuro)
    costo_unit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # auditoría
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["producto", "sucursal", "tipo"]),
            models.Index(fields=["creado_en"]),
        ]

    def save(self, *args, **kwargs):
        """
        IN suma stock, OUT y SALE restan stock.
        """
        if self.tipo == self.IN:
            self.cantidad_signed = int(self.cantidad)
        else:  # OUT o SALE
            self.cantidad_signed = -int(self.cantidad)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} {self.producto_id} x {self.cantidad} @ suc {self.sucursal_id}"


# =========================
#  Ventas
# =========================
class Sale(models.Model):
    sucursal = models.ForeignKey(
        "Branch",
        on_delete=models.PROTECT,
        related_name="ventas"
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        agg = self.items.aggregate(
            s=Sum(
                F("cantidad") * F("precio_unit"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        return agg["s"] or Decimal("0")

    def __str__(self):
        return f"Venta #{self.id} - suc {self.sucursal_id}"


class SaleItem(models.Model):
    venta = models.ForeignKey(Sale, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey("Product", on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()  # entero positivo
    precio_unit = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(cantidad__gte=1),
                name="saleitem_cantidad_gte_1",
            )
        ]

    def __str__(self):
        return f"Item venta {self.venta_id}: {self.producto_id} x {self.cantidad}"
