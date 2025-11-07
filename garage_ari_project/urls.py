"""
URL configuration for garage_ari_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# garage_ari_project/urls.py
# garage_ari_project/urls.py

# garage_ari_project/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView 

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),
    
    # 🛑 API AUTHENTICATION ENDPOINTS (Simple JWT) - The necessary fix
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Endpoints (Master routing)
    path('api/auth/', include('auth_app.urls')), # For custom views like registration/profile
    path('api/clients/', include('clients.urls')),
    path('api/jobcards/', include('jobcards.urls')),
    path('api/inventory/', include('inventory.urls')),
]