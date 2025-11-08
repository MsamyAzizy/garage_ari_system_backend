# garage_ari_project/urls.py (FINAL VERSION FOR ROUTING)

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView 
# 🔑 NEW IMPORT: Import the view from the app where it lives
from clients.views import DashboardMetricsView 

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),
    
    # API AUTHENTICATION ENDPOINTS (Simple JWT)
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 🔑 NEW PATH: The clean, direct dashboard metrics endpoint
    # Full Path: /api/dashboard/metrics/
    path('api/dashboard/metrics/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
    
    # API Endpoints (Master routing)
    path('api/auth/', include('auth_app.urls')), 
    path('api/clients/', include('clients.urls')), # This no longer contains the dashboard path
    path('api/jobcards/', include('jobcards.urls')),
    path('api/inventory/', include('inventory.urls')),
]