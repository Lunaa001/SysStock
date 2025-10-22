from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, F
from django.utils import timezone
from openpyxl import Workbook
from django.http import HttpResponse

from .models import Category, Branch, Product, StockMovement, Sale
from .serializers import (
    CategorySerializer, BranchSerializer,
    ProductSerializer, ProductListSerializer,
    StockMovementSerializer, SaleSerializer
)
from AccountAdmin.permissions import IsAdmin

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("id")
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all().order_by("id")
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id", "name"]
    search_fields    = ["name"]
    ordering_fields  = ["id", "name"]
    ordering         = ["id"]

    @action(detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated, IsAdmin])
    def sales_today(self, request, pk=None):
        branch = self.get_object()
        now    = timezone.localtime()
        start  = now.replace(hour=0, minute=0, second=0, microsecond=0)
        qs     = Sale.objects.filter(sucursal=branch, creado_en__gte=start)
        total  = qs.aggregate(s=Sum(F("items__cantidad") * F("items__precio_unit")))["s"] or 0
        ids    = list(qs.values_list("id", flat=True))
        return Response({"date": start.date(), "branch": {"id": branch.id, "name": branch.name}, "sale_ids": ids, "total": total})

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("categoria").all().order_by("id")
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id", "categoria", "nombre"]
    search_fields    = ["nombre"]
    ordering_fields  = ["id", "nombre", "precio"]
    ordering         = ["id"]

    def get_serializer_class(self):
        return ProductListSerializer if self.action == "list" else ProductSerializer

class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related("producto","sucursal").all().order_by("-creado_en")
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.select_related("sucursal","usuario").all().order_by("-creado_en")
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def low_stock(request):
    threshold = int(request.query_params.get("threshold", 5))
    rows = []
    for p in Product.objects.select_related("categoria","sucursal").all():
        if p.cantidad <= threshold:
            rows.append({
                "id": p.id,
                "producto": p.nombre,
                "categoria": p.categoria.nombre,
                "sucursal": p.sucursal.name,
                "cantidad": p.cantidad,
            })
    return Response({"threshold": threshold, "items": rows})

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated, IsAdmin])
def export_sales_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas"
    ws.append(["ID Venta", "Fecha", "Sucursal", "Producto", "Cantidad", "Precio Unit.", "Total Item"])

    qs = Sale.objects.prefetch_related("items__producto").select_related("sucursal").all()
    for sale in qs:
        for it in sale.items.all():
            ws.append([
                sale.id,
                timezone.localtime(sale.creado_en).strftime("%Y-%m-%d %H:%M"),
                sale.sucursal.name,
                it.producto.nombre,
                int(it.cantidad),
                float(it.precio_unit),
                float(it.cantidad * it.precio_unit),
            ])

    resp = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp['Content-Disposition'] = 'attachment; filename="ventas.xlsx"'
    wb.save(resp)
    return resp
