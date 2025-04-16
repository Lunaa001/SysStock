from django.contrib import admin
from .models import Branch, Provider, Product, User

admin.site.register(Branch)
admin.site.register(Provider)
admin.site.register(Product)
admin.site.register(User)


# Register your models here.
