from django.urls import path, include
from rest_framework import routers
from AccountAdmin import views  

# Importa las vistas de tu aplicación

router= routers.DefaultRouter()
router.register(r'User', views.UserView, basename='Usuario')



urlpatterns = [
    path('AccountAdmin/', include(router.urls)),
    #path('login/', views.LoginView.as_view(), name='login'),  # Ruta para LoginView
    #path('logout/', views.LogoutView.as_view(), name='logout'),  # Ruta para LogoutView
]

