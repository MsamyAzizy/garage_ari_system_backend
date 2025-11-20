from django.contrib import admin
from django.urls import path, include
# ⭐ NEW IMPORTS: Import settings and static for serving media files
from django.conf import settings 
from django.conf.urls.static import static 

from clients.views import DashboardMetricsView 

urlpatterns = [
    # Admin Interface
    path('admin/', admin.site.urls),
    
    # Djoser JWT routes: /api/auth/jwt/create/ (Login) and /api/auth/jwt/refresh/
    path('api/auth/', include('djoser.urls.jwt')), 
    
    # Djoser Core User Management Endpoints: /api/auth/users/ (registration) and /api/auth/users/me/ (profile read/update)
    path('api/auth/', include('djoser.urls')), 
    
    # The clean, direct dashboard metrics endpoint
    # Full Path: /api/dashboard/metrics/
    path('api/dashboard/metrics/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
    
    # API Endpoints (Master routing)
    path('api/clients/', include('clients.urls')), 
    path('api/jobcards/', include('jobcards.urls')),
    path('api/inventory/', include('inventory.urls')),
]

# ⭐ CRITICAL: Add this block to serve media files in development (when DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# ⭐ END CRITICAL BLOCK ⭐