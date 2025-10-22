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
    list_display = ("id", "nombre", "categoria", "sucursal", "precio")
    list_filter = ("categoria", "sucursal")
    search_fields = ("nombre",)

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "producto", "sucursal", "tipo", "cantidad", "usuario", "creado_en")
    list_filter = ("tipo", "sucursal", "producto")
    search_fields = ("producto__nombre", "motivo")

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "sucursal", "usuario", "creado_en", "total")
    inlines = [SaleItemInline]
    date_hierarchy = "creado_en"
