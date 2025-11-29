from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Inclui todas as URLs do app core
    path('', include('core.urls')),
]
