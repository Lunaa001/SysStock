from rest_framework import serializers
from django.db import transaction
from .models import Category, Branch, Product, StockMovement, Sale, SaleItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "nombre"]

class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name"]

class ProductListSerializer(serializers.ModelSerializer):
    categoria = serializers.CharField(source="categoria.nombre", read_only=True)
    cantidad = serializers.IntegerField(read_only=True)  # propiedad @property del modelo
    class Meta:
        model = Product
        fields = ["id", "nombre", "categoria", "precio", "cantidad"]

class ProductSerializer(serializers.ModelSerializer):
    cantidad = serializers.IntegerField(read_only=True)
    class Meta:
        model = Product
        fields = ["id", "nombre", "precio", "categoria", "sucursal", "cantidad"]

class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ["id","producto","sucursal","tipo","cantidad","motivo","usuario","creado_en"]
        read_only_fields = ["usuario","creado_en"]

    def validate(self, data):
        if data.get("tipo") == StockMovement.OUT:
            prod = data["producto"]
            saldo = prod.cantidad
            if data["cantidad"] > max(0, saldo):
                raise serializers.ValidationError("El movimiento dejaría el stock en negativo.")
        return data

    def create(self, validated_data):
        req = self.context.get("request")
        if req and req.user and req.user.is_authenticated:
            validated_data["usuario"] = req.user
        return super().create(validated_data)

class SaleItemInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = ["producto", "cantidad", "precio_unit"]

class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemInlineSerializer(many=True)
    total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    creado_en = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Sale
        fields = ["id", "sucursal", "usuario", "creado_en", "items", "total"]
        read_only_fields = ["usuario", "creado_en", "total"]

    def validate(self, data):
        for it in data["items"]:
            qty = it["cantidad"]
            if qty < 1:
                raise serializers.ValidationError("Cantidad debe ser >= 1")
            prod = it["producto"]
            if qty > max(0, prod.cantidad):
                raise serializers.ValidationError(f"Stock insuficiente para {prod.nombre}. Disponible: {prod.cantidad}")
        return data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        req = self.context.get("request")
        venta = Sale.objects.create(usuario=(req.user if req and req.user.is_authenticated else None), **validated_data)
        for it in items_data:
            item = SaleItem.objects.create(venta=venta, **it)
            StockMovement.objects.create(
                producto=item.producto,
                sucursal=venta.sucursal,
                tipo=StockMovement.OUT,
                cantidad=item.cantidad,
                motivo=f"Venta #{venta.id}",
                usuario=venta.usuario
            )
        return venta
