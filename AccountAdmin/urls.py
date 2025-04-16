from django.urls import path, include
from rest_framework import routers
from AccountAdmin import views  
# Importa las vistas de tu aplicación

router= routers.DefaultRouter()
router.register(r'User', views.UserViewSet, basename='Usuario')



urlpatterns = [
    path('AccountAdmin/', include(router.urls)),
]
