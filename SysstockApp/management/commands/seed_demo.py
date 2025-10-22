from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from SysstockApp.models import Category, Branch, Product, StockMovement, Sale

User = get_user_model()


class Command(BaseCommand):
    help = "Crea datos de demo: admin+2 sucursales, categorías, productos, stock y ventas (con items)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Elimina los datos previos del usuario demo y re-crea todo.",
        )

    def handle(self, *args, **opts):
        self.stdout.write(self.style.MIGRATE_HEADING(">> Seed demo SysStock"))
        with transaction.atomic():
            self._run(force=opts["force"])
        self.stdout.write(self.style.SUCCESS("✔ Demo seed listo."))

    def _run(self, force=False):
        # Admin demo
        username = "demo_admin"
        email = "demo_admin@mail.com"
        password = "1234"

        existing = User.objects.filter(username=username).first()
        if existing and force:
            Branch.objects.filter(owner=existing).delete()
            existing.delete()
            existing = None

        if existing:
            admin = existing
        else:
            admin = User.objects.create_user(username=username, email=email, password=password, rol="admin")

        # Sucursales
        casa, _ = Branch.objects.get_or_create(
            name="Casa Central (DEMO)",
            defaults={"address": "Av Siempre Viva 123", "owner": admin},
        )
        if not casa.owner_id:
            casa.owner = admin
            casa.save()

        norte, _ = Branch.objects.get_or_create(
            name="Sucursal Norte (DEMO)",
            defaults={"address": "Ruta 7 Km 12", "owner": admin},
        )
        if not norte.owner_id:
            norte.owner = admin
            norte.save()

        # Sucursal asignada al admin si tu modelo lo permite
        if getattr(admin, "sucursal_id", None) != casa.id:
            admin.sucursal = casa
            admin.save(update_fields=["sucursal"])

        # Empleados demo
        emp1 = User.objects.filter(username="demo_emp_casa").first()
        if not emp1:
            emp1 = User.objects.create_user("demo_emp_casa", "emp_casa@mail.com", "1234", rol="limMerchant", sucursal=casa)

        emp2 = User.objects.filter(username="demo_emp_norte").first()
        if not emp2:
            emp2 = User.objects.create_user("demo_emp_norte", "emp_norte@mail.com", "1234", rol="limMerchant", sucursal=norte)

        # Categorías
        cat_bebidas, _ = Category.objects.get_or_create(nombre="Bebidas")
        cat_snacks, _ = Category.objects.get_or_create(nombre="Snacks")

        # Crear producto + movimiento de stock inicial (tipo IN)
        def ensure_product(sucursal, nombre, precio, categoria, cantidad_inicial):
            p, _ = Product.objects.get_or_create(
                nombre=nombre,
                sucursal=sucursal,
                defaults={"precio": precio, "categoria": categoria},
            )
            StockMovement.objects.create(
                tipo="in",
                sucursal=sucursal,
                producto=p,
                cantidad=cantidad_inicial,
            )
            return p

        # Productos
        agua_casa = ensure_product(casa, "Agua 500ml (DEMO)", 1000, cat_bebidas, 50)
        cola_casa = ensure_product(casa, "Gaseosa Cola 1.5L (DEMO)", 2500, cat_bebidas, 40)
        papas_casa = ensure_product(casa, "Papas Fritas 90g (DEMO)", 1800, cat_snacks, 35)

        agua_norte = ensure_product(norte, "Agua 500ml (DEMO)", 1100, cat_bebidas, 30)
        cola_norte = ensure_product(norte, "Gaseosa Cola 1.5L (DEMO)", 2600, cat_bebidas, 25)
        papas_norte = ensure_product(norte, "Papas Fritas 90g (DEMO)", 1900, cat_snacks, 20)

        # Helper: crear venta (items con precio_unit, movimiento de salida "out")
        def crear_venta(sucursal, usuario, items, cuando=None):
            v = Sale.objects.create(sucursal=sucursal, usuario=usuario, creado_en=cuando or timezone.now())
            for it in items:
                v.items.create(producto=it["producto"], cantidad=it["cantidad"], precio_unit=it["precio_unit"])
                StockMovement.objects.create(
                    tipo="out",
                    sucursal=sucursal,
                    producto=it["producto"],
                    cantidad=it["cantidad"],
                )
            return v

        # Ventas (algunas hoy, otras en fechas anteriores)
        hoy = timezone.now()
        ayer = hoy - timedelta(days=1)
        hace_5 = hoy - timedelta(days=5)
        hace_12 = hoy - timedelta(days=12)

        crear_venta(casa, admin, [
            {"producto": agua_casa, "cantidad": 2, "precio_unit": agua_casa.precio},
            {"producto": papas_casa, "cantidad": 1, "precio_unit": papas_casa.precio},
        ], cuando=hoy)

        crear_venta(casa, emp1, [
            {"producto": cola_casa, "cantidad": 1, "precio_unit": cola_casa.precio},
        ], cuando=hoy)

        crear_venta(casa, emp1, [
            {"producto": agua_casa, "cantidad": 3, "precio_unit": agua_casa.precio},
        ], cuando=ayer)

        crear_venta(norte, admin, [
            {"producto": agua_norte, "cantidad": 1, "precio_unit": agua_norte.precio},
            {"producto": cola_norte, "cantidad": 1, "precio_unit": cola_norte.precio},
        ], cuando=hoy)

        crear_venta(norte, emp2, [
            {"producto": papas_norte, "cantidad": 2, "precio_unit": papas_norte.precio},
        ], cuando=hace_12)

        self.stdout.write(self.style.SUCCESS("Datos de demo creados."))
        self.stdout.write("Usuarios de prueba:")
        self.stdout.write("  - admin     : demo_admin / 1234")
        self.stdout.write("  - emp casa  : demo_emp_casa / 1234")
        self.stdout.write("  - emp norte : demo_emp_norte / 1234")
