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
    
    # ========== CONFIGURAÇÕES ==========
    path('configuracoes/', views.settings_view, name='settings_view'),
    path('configuracoes/atos/novo/', views.tipo_ato_create, name='tipo_ato_create'),
    path('configuracoes/atos/<int:pk>/editar/', views.tipo_ato_update, name='tipo_ato_update'),
    path('configuracoes/atos/<int:pk>/excluir/', views.tipo_ato_delete, name='tipo_ato_delete'),
    path('configuracoes/atos/<int:pk>/toggle/', views.tipo_ato_toggle, name='tipo_ato_toggle'),
    
    # ========== CLIENTES (CRUD - Sem Exclusão) ==========
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/novo/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/editar/', views.cliente_update, name='cliente_update'),

    # ========== PROTOCOLOS - CERTIDÃO ==========
    path('protocolos/certidao/novo/', views.protocolo_certidao_create, name='protocolo_certidao_create'),
    path('protocolos/certidao/<int:pk>/editar/', views.protocolo_certidao_update, name='protocolo_certidao_update'),
    
    # ========== PROTOCOLOS ==========
    # path('protocolos/', views.protocolo_list, name='protocolo_list'),
    # path('protocolos/ato/novo/', views.protocolo_create_ato, name='protocolo_create_ato'),
    # path('protocolos/<int:pk>/', views.protocolo_detail, name='protocolo_detail'),
    
    # ========== API ==========
    path('api/buscar-cliente/', views.api_buscar_cliente, name='api_buscar_cliente'),
]

