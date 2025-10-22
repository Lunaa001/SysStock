# SysstockApp/views.py

# =========================
# IMPORTS
# =========================
from rest_framework import viewsets, permissions, filters, status  # MOD (quitamos serializers aquí; no se usa)
from rest_framework.exceptions import PermissionDenied  # NUEVO (para perform_create en BranchViewSet)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from django.db import transaction
from django.utils import timezone
from django.utils.timezone import localdate
from datetime import datetime, time   # MOD (agregamos time para rangos de día)

from openpyxl import Workbook
from django.http import HttpResponse

from django.db.models import Sum

# (Dejamos importadas funciones/fields adicionales si luego las querés usar en reportes avanzados)
# from django.db.models import F, DecimalField, ExpressionWrapper
# from django.db.models.functions import TruncDate

from .models import Category, Branch, Product, StockMovement, Sale
from .serializers import (
    CategorySerializer,
    BranchSerializer,
    ProductSerializer,
    StockMovementSerializer,
    SaleSerializer,
)
from AccountAdmin.permissions import IsAdmin


# =========================
# HELPERS DE TENANT / SCOPE
# =========================
def _scope_branches(qs, user):
    """
    - superuser: ve todo
    - admin: ve solo sucursales donde es owner
    - limMerchant: solo su sucursal asignada
    """
    if getattr(user, "is_superuser", False):
        return qs
    if getattr(user, "rol", None) == "admin":
        return qs.filter(owner=user)
    # limMerchant
    return qs.filter(pk=user.sucursal_id)


def _scope_by_branch_on_model(qs, user, branch_field="sucursal"):
    """
    Para modelos con FK a sucursal (p.ej., Product.sucursal, Sale.sucursal):
    - superuser: todo
    - admin: {branch_field}__owner = user
    - limMerchant: {branch_field} = user.sucursal
    """
    if getattr(user, "is_superuser", False):
        return qs
    if getattr(user, "rol", None) == "admin":
        return qs.filter(**{f"{branch_field}__owner": user})
    return qs.filter(**{f"{branch_field}__id": user.sucursal_id})


# =========================
# HELPER DE STOCK (por movimientos)  # NUEVO
# =========================
def _stock_actual_producto(producto: Product) -> int:
    """
    Calcula stock actual por producto como:
    stock = ENTRADAS ('in') - SALIDAS ('out')
    """
    entradas = StockMovement.objects.filter(producto=producto, tipo="in").aggregate(total=Sum("cantidad"))["total"] or 0
    salidas  = StockMovement.objects.filter(producto=producto, tipo="out").aggregate(total=Sum("cantidad"))["total"] or 0
    return int(entradas - salidas)


# =========================
# SUCURSALES
# =========================
class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Branch.objects.all().order_by("id")
        return _scope_branches(qs, self.request.user)

    def perform_create(self, serializer):
        """
        Guarda owner=admin que crea la sucursal (si no, luego no aparece en /api/sucursales/ del admin).
        """
        user = self.request.user
        if getattr(user, "rol", None) != "admin":
            raise PermissionDenied("Solo un admin puede crear sucursales.")
        serializer.save(owner=user)  # MOD (clave)

    # -------------------------
    # /api/sucursales/<id>/ventas_rango/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    # -------------------------
    @action(detail=True, methods=["get"], url_path="ventas_rango")
    def ventas_rango(self, request, pk=None):
        branch = self.get_object()
        user = request.user

        # Permisos
        if getattr(user, "rol", None) == "limMerchant" and user.sucursal_id != branch.id:
            return Response({"detail": "No tienes permiso para ver esta sucursal."}, status=403)
        if getattr(user, "rol", None) == "admin" and branch.owner_id != user.id:
            return Response({"detail": "Esta sucursal no pertenece a tu cuenta."}, status=403)

        # Parámetros requeridos
        desde_str = request.query_params.get("desde")
        hasta_str = request.query_params.get("hasta")
        if not desde_str or not hasta_str:
            return Response(
                {"detail": "Parámetros requeridos: desde=YYYY-MM-DD & hasta=YYYY-MM-DD"},
                status=400
            )

        # Parseo correcto de fechas
        try:
            desde_date = datetime.strptime(desde_str, "%Y-%m-%d").date()
            hasta_date = datetime.strptime(hasta_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "Formato inválido. Usa YYYY-MM-DD."}, status=400)

        if hasta_date < desde_date:
            return Response({"detail": "`hasta` no puede ser anterior a `desde`."}, status=400)

        # Rango completo por día [00:00:00, 23:59:59]  # MOD
        desde_dt = datetime.combine(desde_date, time.min)
        hasta_dt = datetime.combine(hasta_date, time.max)

        # Ventas del rango
        ventas = (
            Sale.objects.filter(sucursal=branch, creado_en__range=(desde_dt, hasta_dt))
            .prefetch_related("items__producto")
            .select_related("sucursal")
            .order_by("creado_en")
        )

        def total_venta(venta):
            return sum(it.cantidad * it.precio_unit for it in venta.items.all())

        monto_total = 0.0
        data = []

        for v in ventas:
            tv = float(total_venta(v))
            monto_total += tv
            data.append({
                "venta_id": v.id,
                "fecha_hora": v.creado_en,
                "total_venta": tv,
                "items": [
                    {
                        "producto": it.producto.nombre if it.producto else None,
                        "cantidad": it.cantidad,
                        "precio_unit": float(it.precio_unit),
                        "total_item": float(it.cantidad * it.precio_unit)
                    } for it in v.items.all()
                ]
            })

        return Response({
            "sucursal": branch.name,
            "desde": desde_str,
            "hasta": hasta_str,
            "monto_total": float(monto_total),
            "ventas": data
        })

    # -------------------------
    # /api/sucursales/<id>/ventas_por_producto/?desde=&hasta=
    # -------------------------
    @action(detail=True, methods=["get"], url_path="ventas_por_producto")
    def ventas_por_producto(self, request, pk=None):
        branch = self.get_object()
        u = request.user
        if getattr(u, "rol", None) == "limMerchant" and u.sucursal_id != branch.id:
            return Response({"detail": "No tienes permiso para esta sucursal."}, status=403)
        if getattr(u, "rol", None) == "admin" and branch.owner_id != u.id:
            return Response({"detail": "Esta sucursal no te pertenece."}, status=403)

        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")
        qs = Sale.objects.filter(sucursal=branch).prefetch_related("items__producto")
        if desde and hasta:
            qs = qs.filter(creado_en__date__range=(desde, hasta))

        agg = {}
        for v in qs:
            for it in v.items.all():
                pid = getattr(it.producto, "id", None)
                pname = getattr(it.producto, "nombre", None)
                if pid is None:
                    continue
                if pid not in agg:
                    agg[pid] = {"producto_id": pid, "producto": pname, "cantidad": 0, "monto": 0.0}
                agg[pid]["cantidad"] += it.cantidad
                agg[pid]["monto"] += float(it.cantidad * it.precio_unit)

        result = sorted(agg.values(), key=lambda x: x["monto"], reverse=True)
        return Response({
            "sucursal": branch.name,
            "desde": desde,
            "hasta": hasta,
            "resumen": result,
        })

    # -------------------------
    # /api/sucursales/<id>/ventas_por_dia/?desde=&hasta=
    # -------------------------
    @action(detail=True, methods=["get"], url_path="ventas_por_dia")
    def ventas_por_dia(self, request, pk=None):
        branch = self.get_object()
        u = request.user
        if getattr(u, "rol", None) == "limMerchant" and u.sucursal_id != branch.id:
            return Response({"detail": "No tienes permiso para esta sucursal."}, status=403)
        if getattr(u, "rol", None) == "admin" and branch.owner_id != u.id:
            return Response({"detail": "Esta sucursal no te pertenece."}, status=403)

        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")
        qs = Sale.objects.filter(sucursal=branch)
        if desde and hasta:
            qs = qs.filter(creado_en__date__range=(desde, hasta))

        # sumar total por día
        series = {}
        for v in qs.prefetch_related("items"):
            d = v.creado_en.date()
            tot = sum(it.cantidad * it.precio_unit for it in v.items.all())
            series[d] = series.get(d, 0.0) + float(tot)

        rows = [{"fecha": str(k), "monto": v} for k, v in sorted(series.items())]
        total = sum(x["monto"] for x in rows)

        return Response({
            "sucursal": branch.name,
            "desde": desde,
            "hasta": hasta,
            "monto_total": total,
            "serie": rows,
        })

    # -------------------------
    # /api/sucursales/<id>/ventas_export/xlsx/?desde=&hasta=
    # -------------------------
    @action(detail=True, methods=["get"], url_path="ventas_export/xlsx")
    def ventas_export_xlsx(self, request, pk=None):
        branch = self.get_object()
        u = request.user

        # Permisos
        if getattr(u, "rol", None) == "limMerchant" and u.sucursal_id != branch.id:
            return Response({"detail": "No tienes permiso para esta sucursal."}, status=403)
        if getattr(u, "rol", None) == "admin" and branch.owner_id != u.id:
            return Response({"detail": "Esta sucursal no te pertenece."}, status=403)

        # Filtros opcionales de fecha
        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")

        qs = (
            Sale.objects
            .filter(sucursal=branch)
            .prefetch_related("items__producto")
            .select_related("sucursal")
            .order_by("creado_en")
        )
        if desde and hasta:
            qs = qs.filter(creado_en__date__range=(desde, hasta))

        # Armar Excel
        wb = Workbook()
        ws = wb.active
        ws.title = f"Ventas {branch.name}"
        ws.append(["ID Venta", "Fecha/Hora", "Sucursal", "Producto", "Cantidad", "Precio Unit.", "Total Item"])

        for sale in qs:
            for it in sale.items.all():
                ws.append([
                    sale.id,
                    timezone.localtime(sale.creado_en).strftime("%Y-%m-%d %H:%M"),
                    branch.name,
                    getattr(it.producto, "nombre", None),
                    int(it.cantidad),
                    float(it.precio_unit),
                    float(it.cantidad * it.precio_unit),
                ])

        resp = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f'ventas_{branch.id}.xlsx'
        resp['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(resp)
        return resp

    # -------------------------
    # /api/sucursales/<id>/resumen/?threshold=5&limit=50
    # -------------------------
    @action(detail=True, methods=["get"], url_path="resumen")
    def resumen(self, request, pk=None):
        """
        Resumen reducido (usa stock REAL por movimientos, no Product.cantidad).
        - ventas_hoy.monto
        - productos_bajo_stock (stock real calculado)
        """
        branch = self.get_object()
        u = request.user

        # Permisos
        if getattr(u, "rol", None) == "limMerchant" and u.sucursal_id != branch.id:
            return Response({"detail": "No tienes permiso para esta sucursal."}, status=403)
        if getattr(u, "rol", None) == "admin" and branch.owner_id != u.id:
            return Response({"detail": "Esta sucursal no te pertenece."}, status=403)

        hoy = localdate()

        # Ventas HOY (monto)
        ventas_hoy_qs = Sale.objects.filter(sucursal=branch, creado_en__date=hoy).prefetch_related("items")
        ventas_hoy_monto = float(sum(
            sum(it.cantidad * it.precio_unit for it in v.items.all()) for v in ventas_hoy_qs
        ))

        # Threshold de bajo stock
        try:
            threshold = int(request.query_params.get("threshold", 5))
        except ValueError:
            threshold = 5

        # Stock bajo (por movimientos)  # MOD
        productos_bajo_stock = []
        for p in Product.objects.filter(sucursal=branch).select_related("categoria"):
            stock_actual = _stock_actual_producto(p)
            if stock_actual <= threshold:
                productos_bajo_stock.append({
                    "id": p.id,
                    "nombre": p.nombre,
                    "categoria": p.categoria.nombre if p.categoria else None,
                    "stock": stock_actual
                })

        return Response({
            "sucursal": branch.name,
            "fecha_hoy": str(hoy),
            "ventas_hoy": {"monto": ventas_hoy_monto},
            "threshold": threshold,
            "productos_bajo_stock": productos_bajo_stock
        })

    # -------------------------
    # DELETE /api/sucursales/<id>/  (borra TODO + limMerchants de esa sucursal)
    # -------------------------
    def destroy(self, request, *args, **kwargs):
        branch = self.get_object()
        user = request.user

        # Permisos
        if getattr(user, "rol", None) == "limMerchant":
            return Response({"detail": "No puedes borrar sucursales."}, status=403)
        if getattr(user, "rol", None) == "admin" and branch.owner_id != user.id:
            return Response({"detail": "Esta sucursal no te pertenece."}, status=403)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        with transaction.atomic():
            # Borrar empleados limMerchant de esta sucursal
            User.objects.filter(rol="limMerchant", sucursal_id=branch.id).delete()
            # Borrar sucursal (lo demás cae por CASCADE si los FKs están bien)
            branch.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


# =========================
# CATEGORÍAS
# =========================
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id", "nombre"]
    search_fields = ["nombre"]
    ordering_fields = ["id", "nombre"]
    ordering = ["id"]

    def get_queryset(self):
        # Si Category no está atada a sucursal, se puede dejar global
        # Si querés ligarla a sucursal/empresa, relacioná Category con Branch y usa _scope_by_branch_on_model
        return Category.objects.all().order_by("id")


# =========================
# PRODUCTOS
# =========================
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id", "categoria", "nombre", "sucursal"]
    search_fields = ["nombre"]
    ordering_fields = ["id", "nombre", "precio"]
    ordering = ["id"]

    def get_queryset(self):
        qs = Product.objects.select_related("categoria", "sucursal").all().order_by("id")
        return _scope_by_branch_on_model(qs, self.request.user, branch_field="sucursal")


# =========================
# MOVIMIENTOS DE STOCK
# =========================
class StockMovementViewSet(viewsets.ModelViewSet):
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id", "tipo", "sucursal", "producto"]
    search_fields = ["producto__nombre"]
    ordering_fields = ["id", "creado_en"]
    ordering = ["-creado_en"]

    def get_queryset(self):
        qs = (
            StockMovement.objects
            .select_related("producto", "sucursal")
            .all()
            .order_by("-creado_en")
        )
        return _scope_by_branch_on_model(qs, self.request.user, branch_field="sucursal")


# =========================
# VENTAS
# =========================
class SaleViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id", "sucursal"]
    ordering_fields = ["id", "creado_en"]
    ordering = ["-creado_en"]

    def get_queryset(self):
        qs = (
            Sale.objects
            .select_related("sucursal", "usuario")
            .prefetch_related("items__producto")
            .all()
            .order_by("-creado_en")
        )
        return _scope_by_branch_on_model(qs, self.request.user, branch_field="sucursal")


# =========================
# BAJO STOCK (endpoint suelto)  # MOD (usa movimientos en vez de Product.cantidad)
# =========================
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def low_stock(request):
    """
    Lista productos con stock <= threshold (por movimientos).
    Query params:
      - threshold: int (default 5)
      - limit:     int (default 50)
    """
    try:
        threshold = int(request.query_params.get("threshold", 5))
    except ValueError:
        threshold = 5

    try:
        limit = int(request.query_params.get("limit", 50))
    except ValueError:
        limit = 50

    qs = Product.objects.select_related("categoria", "sucursal").all()
    qs = _scope_by_branch_on_model(qs, request.user, branch_field="sucursal")

    rows = []
    for p in qs:
        stock_actual = _stock_actual_producto(p)
        if stock_actual <= threshold:
            rows.append({
                "id": p.id,
                "producto": p.nombre,
                "categoria": p.categoria.nombre if p.categoria else None,
                "sucursal": p.sucursal.name if p.sucursal else None,
                "stock": stock_actual,
            })

    rows = rows[:limit]
    return Response({"threshold": threshold, "items": rows})


# =========================
# EXPORTAR VENTAS A EXCEL (solo admin, con scoping)
# =========================
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated, IsAdmin])
def export_sales_excel(request):
    # Scope por owner=admin
    qs = (
        Sale.objects
        .prefetch_related("items__producto")
        .select_related("sucursal")
        .all()
    )
    qs = _scope_by_branch_on_model(qs, request.user, branch_field="sucursal")

    wb = Workbook()
    ws = wb.active
    ws.title = "Ventas"
    ws.append(["ID Venta", "Fecha", "Sucursal", "Producto", "Cantidad", "Precio Unit.", "Total Item"])

    for sale in qs:
        for it in sale.items.all():
            ws.append([
                sale.id,
                timezone.localtime(sale.creado_en).strftime("%Y-%m-%d %H:%M"),
                sale.sucursal.name if sale.sucursal else None,
                it.producto.nombre if getattr(it, "producto", None) else None,
                int(it.cantidad),
                float(it.precio_unit),
                float(it.cantidad * it.precio_unit),
            ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="ventas.xlsx"'
    wb.save(response)
    return response
