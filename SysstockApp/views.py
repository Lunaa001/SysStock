from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Sum, F
from django.http import HttpResponse
from openpyxl import Workbook
from io import BytesIO

from .models import Category, Branch, Product, StockMovement, Sale, SaleItem
from .serializer import (
    CategorySerializer, BranchSerializer,
    ProductSerializer, ProductListSerializer,
    StockMovementSerializer, SaleSerializer
)
from .permissions import IsAdmin

# Scope por sucursal para limMerchant
def _scope_by_role(queryset, request, field='sucursal'):
    user = request.user
    if getattr(user, 'rol', '') == 'limMerchant' and user.sucursal:
        kw = {f"{field}__name": user.sucursal}
        return queryset.filter(**kw)
    return queryset

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("nombre")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["nombre"]
    ordering_fields = ["nombre"]

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all().order_by("name")
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name"]

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "id": ["exact", "in"],
        "categoria": ["exact"],
        "sucursal": ["exact"],
        "precio": ["gte", "lte"],
    }
    search_fields = ["nombre", "categoria__nombre"]
    ordering_fields = ["id", "nombre", "precio"]
    ordering = ["id"]

    def get_queryset(self):
        qs = Product.objects.select_related("categoria","sucursal").all().order_by("id")
        return _scope_by_role(qs, self.request, field="sucursal")

    def get_serializer_class(self):
        return ProductListSerializer if self.action == "list" else ProductSerializer

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        umbral = int(request.query_params.get("umbral", 5))
        data = []
        for p in self.get_queryset():
            if p.cantidad <= umbral:
                data.append({
                    "id": p.id, "nombre": p.nombre, "categoria": p.categoria.nombre,
                    "precio": str(p.precio), "cantidad": p.cantidad
                })
        return Response(data)

class StockMovementViewSet(viewsets.ModelViewSet):
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        qs = StockMovement.objects.select_related("producto","sucursal","usuario").all().order_by("-creado_en")
        return _scope_by_role(qs, self.request, field="sucursal")

class SaleViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {"sucursal": ["exact"]}
    search_fields = ["items__producto__nombre"]
    ordering_fields = ["creado_en"]
    ordering = ["-creado_en"]

    def get_queryset(self):
        qs = Sale.objects.select_related("sucursal","usuario").prefetch_related("items__producto").all().order_by("-creado_en")
        return _scope_by_role(qs, self.request, field="sucursal")

    def create(self, request, *args, **kwargs):
        resp = super().create(request, *args, **kwargs)
        # avisos de bajo stock
        low = []
        venta_id = resp.data["id"]
        venta = self.get_queryset().get(pk=venta_id)
        for it in venta.items.all():
            p = it.producto
            if p.cantidad <= 5:
                low.append({"id": p.id, "nombre": p.nombre, "cantidad": p.cantidad})
        resp.data["low_stock_warnings"] = low
        return resp

    @action(detail=False, methods=["get"])
    def resumen_diario(self, request):
        tznow = timezone.localtime()
        start = tznow.replace(hour=0, minute=0, second=0, microsecond=0)
        end = tznow.replace(hour=23, minute=59, second=59, microsecond=999999)
        qs = self.get_queryset().filter(creado_en__range=(start, end))
        ventas = [{
            "id": v.id,
            "hora": timezone.localtime(v.creado_en).strftime("%H:%M:%S"),
            "sucursal": v.sucursal.name,
            "total": str(v.total),
            "items": [{
                "producto": it.producto.nombre,
                "cantidad": it.cantidad,
                "precio_unit": str(it.precio_unit),
                "subtotal": str(it.cantidad * it.precio_unit)
            } for it in v.items.all()]
        } for v in qs]
        total_dia = sum([v.total for v in qs])
        return Response({"fecha": tznow.date().isoformat(), "ventas": ventas, "total_dia": str(total_dia)})

    @action(detail=False, methods=["get"])
    def top_productos(self, request):
        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")
        limit = int(request.query_params.get("limit", 5))
        items = SaleItem.objects.select_related("producto", "venta")
        items = _scope_by_role(items, request, field="venta__sucursal")
        if desde:
            items = items.filter(venta__creado_en__date__gte=desde)
        if hasta:
            items = items.filter(venta__creado_en__date__lte=hasta)
        agg = (items.values("producto_id", "producto__nombre")
                    .annotate(unidades=Sum("cantidad"),
                              ingresos=Sum(F("cantidad") * F("precio_unit")))
                    .order_by("-unidades")[:limit])
        data = [{"producto_id": a["producto_id"], "nombre": a["producto__nombre"],
                 "unidades": a["unidades"], "ingresos": str(a["ingresos"] or 0)} for a in agg]
        return Response(data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsAdmin])
    def exportar_excel(self, request):
        # Solo admin
        fecha = request.query_params.get("fecha")
        if fecha:
            y, m, d = map(int, fecha.split("-"))
            start = timezone.make_aware(timezone.datetime(y, m, d, 0, 0, 0))
            end = timezone.make_aware(timezone.datetime(y, m, d, 23, 59, 59, 999999))
        else:
            tznow = timezone.localtime()
            start = tznow.replace(hour=0, minute=0, second=0, microsecond=0)
            end = tznow.replace(hour=23, minute=59, second=59, microsecond=999999)
        qs = self.get_queryset().filter(creado_en__range=(start, end))

        wb = Workbook(); ws = wb.active; ws.title = "Ventas"
        ws.append(["VentaID", "FechaHora", "Sucursal", "Producto", "Cantidad", "PrecioUnit", "Subtotal"])
        for v in qs:
            for it in v.items.all():
                subtotal = it.cantidad * it.precio_unit
                ws.append([
                    v.id,
                    timezone.localtime(v.creado_en).strftime("%Y-%m-%d %H:%M:%S"),
                    v.sucursal.name,
                    it.producto.nombre,
                    it.cantidad,
                    float(it.precio_unit),
                    float(subtotal)
                ])
        ws.append([]); ws.append(["", "", "", "", "TOTAL DÍA", "", float(sum([float(v.total) for v in qs]))])

        stream = BytesIO(); wb.save(stream); stream.seek(0)
        resp = HttpResponse(stream.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        fname = f"ventas_{(fecha or timezone.localtime().date().isoformat())}.xlsx"
        resp["Content-Disposition"] = f'attachment; filename="{fname}"'
        return resp
