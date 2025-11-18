from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from .models import (
    Category,
    Branch,
    Product,
    StockMovement,
    Sale,
    SaleItem,
)


# =========================
#  Categorías
# =========================
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "nombre"]

    def validate_nombre(self, value):
        if value and value.isdigit():
            raise serializers.ValidationError("El nombre no puede ser solo números.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return attrs

        nombre = attrs.get("nombre", getattr(self.instance, "nombre", None))
        user = request.user

        if getattr(user, "rol", None) == "admin":
            owner = user
        elif getattr(user, "rol", None) == "limMerchant":
            suc = getattr(user, "sucursal", None)
            if not suc or not getattr(suc, "owner", None):
                raise serializers.ValidationError({"detail": "Tu usuario no tiene una sucursal asignada."})
            owner = suc.owner
        else:
            owner = user

        qs = Category.objects.filter(owner=owner, nombre__iexact=nombre)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError({"nombre": "Ya existe una categoría con ese nombre en tu empresa."})
        self._resolved_owner = owner
        return attrs

    def create(self, validated_data):
        owner = getattr(self, "_resolved_owner", None)
        if owner is None:
            request = self.context.get("request")
            if request and request.user.is_authenticated:
                if getattr(request.user, "rol", None) == "admin":
                    owner = request.user
                elif getattr(request.user, "rol", None) == "limMerchant":
                    owner = request.user.sucursal.owner
                else:
                    owner = request.user
        return Category.objects.create(owner=owner, **validated_data)


# =========================
#  Sucursales
# =========================
class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "address", "telefono"]
        read_only_fields = ["id"]

    def validate_name(self, value):
        if value and value.isdigit():
            raise serializers.ValidationError("El nombre no puede ser solo números.")
        return value


# =========================
#  Productos (stock_actual + SKU + stock_min)
# =========================
class ProductSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)
    sucursal_nombre = serializers.CharField(source="sucursal.name", read_only=True)
    stock_actual = serializers.SerializerMethodField()

    sku = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    stock_min = serializers.IntegerField(required=False, allow_null=True, min_value=0)

    class Meta:
        model = Product
        fields = [
            "id",
            "nombre",
            "precio",
            "categoria",
            "categoria_nombre",
            "sucursal",
            "sucursal_nombre",
            "stock_actual",
            "sku",
            "stock_min",
        ]
        read_only_fields = ["id", "categoria_nombre", "sucursal_nombre", "stock_actual"]

    def get_stock_actual(self, obj):
        tot_in = (
            StockMovement.objects.filter(producto=obj, sucursal=obj.sucursal, tipo="IN")
            .aggregate(s=Sum("cantidad"))
            .get("s")
            or 0
        )
        tot_out = (
            StockMovement.objects.filter(producto=obj, sucursal=obj.sucursal, tipo="OUT")
            .aggregate(s=Sum("cantidad"))
            .get("s")
            or 0
        )
        return int(tot_in - tot_out)

    def validate_nombre(self, value):
        if value and value.isdigit():
            raise serializers.ValidationError("El nombre no puede ser solo números.")
        return value

    def validate_precio(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0.")
        return value

    def validate(self, attrs):
        # Evitar duplicados por nombre dentro de la sucursal
        nombre = attrs.get("nombre", getattr(self.instance, "nombre", None))
        sucursal = attrs.get("sucursal", getattr(self.instance, "sucursal", None))
        if nombre and sucursal:
            qs = Product.objects.filter(nombre__iexact=nombre, sucursal=sucursal)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"nombre": "Ya existe un producto con este nombre en esta sucursal."})

        # SKU obligatorio SOLO al crear
        creating = self.instance is None
        sku = attrs.get("sku", getattr(self.instance, "sku", None))
        if creating and not sku:
            raise serializers.ValidationError({"sku": "El SKU es obligatorio al crear el producto."})

        # Unicidad de SKU por empresa (owner)
        if sku:
            request = self.context.get("request")
            if request and request.user and request.user.is_authenticated:
                user = request.user
                if getattr(user, "rol", None) == "admin":
                    owner = user
                elif getattr(user, "rol", None) == "limMerchant":
                    suc = getattr(user, "sucursal", None)
                    owner = suc.owner if suc else None
                else:
                    owner = user
                if owner and sucursal:
                    qs = Product.objects.filter(sucursal__owner=owner, sku__iexact=sku)
                    if self.instance:
                        qs = qs.exclude(pk=self.instance.pk)
                    if qs.exists():
                        raise serializers.ValidationError({"sku": "Este SKU ya existe en tu empresa."})
        return attrs


# =========================
#  Campo custom para mapear ES -> IN/OUT
# =========================
class TipoMovimientoField(serializers.ChoiceField):
    MAP = {
        "IN": "IN",
        "INGRESO": "IN",
        "ENTRADA": "IN",
        "OUT": "OUT",
        "EGRESO": "OUT",
        "SALIDA": "OUT",
    }

    def to_internal_value(self, data):
        if data is None:
            return super().to_internal_value(data)
        key = str(data).strip().upper()
        mapped = self.MAP.get(key)
        if mapped is None:
            raise serializers.ValidationError("Valor inválido. Usa 'INGRESO' o 'EGRESO'.")
        return super().to_internal_value(mapped)


# =========================
#  Movimientos de stock
# =========================
class StockMovementSerializer(serializers.ModelSerializer):
    tipo = TipoMovimientoField(choices=("IN", "OUT"))
    cantidad = serializers.IntegerField(min_value=1)  # entero positivo
    motivo = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    costo_unit = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)

    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    sucursal_nombre = serializers.CharField(source="sucursal.name", read_only=True)
    usuario_username = serializers.CharField(source="usuario.username", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "tipo",
            "cantidad",
            "motivo",
            "costo_unit",
            "producto",
            "sucursal",
            "usuario",
            "usuario_username",
            "producto_nombre",
            "sucursal_nombre",
            "creado_en",
        ]
        read_only_fields = [
            "id",
            "usuario",
            "usuario_username",
            "producto_nombre",
            "sucursal_nombre",
            "creado_en",
        ]

    def validate(self, attrs):
        # OUT no puede superar stock disponible
        producto = attrs.get("producto")
        sucursal = attrs.get("sucursal")
        cantidad = attrs.get("cantidad")
        tipo = attrs.get("tipo")

        if not producto or not sucursal or not tipo:
            return attrs

        if tipo == "OUT":
            tot_in = (
                StockMovement.objects.filter(producto=producto, sucursal=sucursal, tipo="IN")
                .aggregate(s=Sum("cantidad"))
                .get("s")
                or 0
            )
            tot_out = (
                StockMovement.objects.filter(producto=producto, sucursal=sucursal, tipo="OUT")
                .aggregate(s=Sum("cantidad"))
                .get("s")
                or 0
            )
            disponible = tot_in - tot_out
            if cantidad > disponible:
                raise serializers.ValidationError({"cantidad": f"Stock insuficiente. Disponible: {disponible}"})
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["usuario"] = request.user
        return super().create(validated_data)


# =========================
#  Ventas (crea items y OUT automáticos)
# =========================
class SaleItemSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    cantidad = serializers.IntegerField(min_value=1)  # entero positivo

    # 🔑 ahora es opcional, puede venir vacío y se toma del producto
    precio_unit = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = SaleItem
        fields = ["id", "producto", "producto_nombre", "cantidad", "precio_unit"]
        read_only_fields = ["id", "producto_nombre"]
        extra_kwargs = {
            "precio_unit": {"required": False},
        }

    def validate_precio_unit(self, value):
        # solo validamos si viene; si no, se toma product.precio en create()
        if value is not None and value <= 0:
            raise serializers.ValidationError("El precio unitario debe ser mayor a 0.")
        return value


class SaleSerializer(serializers.ModelSerializer):
    """
    Crea la venta y sus items.
    Por cada item, registra automáticamente un movimiento OUT.
    """
    items = SaleItemSerializer(many=True, required=True)
    sucursal_nombre = serializers.CharField(source="sucursal.name", read_only=True)
    usuario_username = serializers.CharField(source="usuario.username", read_only=True)

    class Meta:
        model = Sale
        fields = ["id", "sucursal", "sucursal_nombre", "usuario", "usuario_username", "creado_en", "items"]
        read_only_fields = ["id", "usuario", "usuario_username", "creado_en", "sucursal_nombre"]

    def validate(self, attrs):
        sucursal = attrs.get("sucursal", getattr(self.instance, "sucursal", None))
        items = self.initial_data.get("items", [])

        if not items or not isinstance(items, list):
            raise serializers.ValidationError({"items": "Debes enviar al menos un ítem."})
        if not sucursal:
            raise serializers.ValidationError({"sucursal": "Sucursal requerida."})

        for raw in items:
            producto_id = raw.get("producto")
            cantidad = raw.get("cantidad")
            if not producto_id or not cantidad:
                raise serializers.ValidationError("Cada ítem requiere 'producto' y 'cantidad'.")

            try:
                producto = Product.objects.get(pk=producto_id)
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Producto inválido: {producto_id}")

            if producto.sucursal_id != sucursal.id:
                raise serializers.ValidationError("El producto no pertenece a esta sucursal.")

            tot_in = (
                StockMovement.objects.filter(producto=producto, sucursal=sucursal, tipo="IN")
                .aggregate(s=Sum("cantidad"))
                .get("s")
                or 0
            )
            tot_out = (
                StockMovement.objects.filter(producto=producto, sucursal=sucursal, tipo="OUT")
                .aggregate(s=Sum("cantidad"))
                .get("s")
                or 0
            )
            disponible = tot_in - tot_out
            if cantidad > disponible:
                raise serializers.ValidationError(
                    f"Stock insuficiente para '{producto.nombre}'. Disponible: {disponible}"
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["usuario"] = request.user

        venta = Sale.objects.create(**validated_data)

        for it in items_data:
            producto = (
                it["producto"] if isinstance(it["producto"], Product)
                else Product.objects.get(pk=it["producto"])
            )
            cantidad = it["cantidad"]
            # 👉 si no viene precio_unit, usamos producto.precio
            precio_unit = it.get("precio_unit") or producto.precio

            # Crear item
            SaleItem.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unit=precio_unit,
            )

            # Registrar salida de stock por cada item
            StockMovement.objects.create(
                tipo="OUT",
                cantidad=cantidad,
                motivo=f"Venta #{venta.id} - {producto.nombre}",
                producto=producto,
                sucursal=venta.sucursal,
                usuario=validated_data.get("usuario"),
            )

        return venta
