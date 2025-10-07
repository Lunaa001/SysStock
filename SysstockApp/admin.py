from django.contrib import admin
from .models import Category, Branch, Product, StockMovement, Sale, SaleItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "get_categoria", "precio", "get_cantidad", "sucursal")
    list_filter = ("categoria", "sucursal")
    search_fields = ("nombre", "categoria__nombre")
    ordering = ("id",)

    def get_categoria(self, obj):
        return obj.categoria.nombre
    get_categoria.short_description = "Categoría"

    def get_cantidad(self, obj):
        return obj.cantidad
    get_cantidad.short_description = "Cantidad"

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "producto", "sucursal", "tipo", "cantidad", "usuario", "creado_en")
    list_filter = ("tipo", "sucursal", "producto")
    search_fields = ("producto__nombre",)

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ("producto", "cantidad", "precio_unit")

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "sucursal", "usuario", "creado_en", "total")
    list_filter = ("sucursal", "creado_en")
    date_hierarchy = "creado_en"
    inlines = [SaleItemInline]
