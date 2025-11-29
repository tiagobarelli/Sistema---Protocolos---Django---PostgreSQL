from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LogoutView # Importe o LogoutView
from core.views import CustomLoginView, setup_system, dashboard # Importe o dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rota de Login Específica
    path('login/', CustomLoginView.as_view(), name='login'),
    
    # Rota de Logout
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Rota de Setup
    path('setup/', setup_system, name='setup_system'),
    
    # A HOME agora aponta para o Dashboard, não para o Login
    path('', dashboard, name='home'), 
]