from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # ========== AUTENTICAÇÃO ==========
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('setup/', views.setup_system, name='setup_system'),
    
    # ========== HOME ==========
    path('', views.home, name='home'),
    
    # ========== USUÁRIOS (CRUD) ==========
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/novo/', views.user_create, name='user_create'),
    path('usuarios/<int:pk>/editar/', views.user_update, name='user_update'),
    path('usuarios/<int:pk>/excluir/', views.user_delete, name='user_delete'),
    
    # ========== CLIENTES (CRUD) ==========
    # path('clientes/', views.cliente_list, name='cliente_list'),
    # path('clientes/novo/', views.cliente_create, name='cliente_create'),
    # path('clientes/<int:pk>/', views.cliente_detail, name='cliente_detail'),
    # path('clientes/<int:pk>/editar/', views.cliente_update, name='cliente_update'),
    # path('clientes/<int:pk>/excluir/', views.cliente_delete, name='cliente_delete'),
    
    # ========== PROTOCOLOS ==========
    # path('protocolos/', views.protocolo_list, name='protocolo_list'),
    # path('protocolos/ato/novo/', views.protocolo_create_ato, name='protocolo_create_ato'),
    # path('protocolos/certidao/novo/', views.protocolo_create_certidao, name='protocolo_create_certidao'),
    # path('protocolos/<int:pk>/', views.protocolo_detail, name='protocolo_detail'),
    
    # ========== API (para Vue.js) ==========
    # path('api/clientes/', views.api_clientes, name='api_clientes'),
]

