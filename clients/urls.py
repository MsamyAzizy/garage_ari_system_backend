# clients/urls.py

from rest_framework_nested import routers
from django.urls import path, include
from .views import ClientViewSet, VehicleViewSet 

# --- Setup for Client/Vehicle Routing ---
router = routers.DefaultRouter()
router.register(r'', ClientViewSet, basename='client')

# 🛑 ONLY use nested router for vehicles
clients_router = routers.NestedDefaultRouter(router, r'', lookup='client')
clients_router.register(r'vehicles', VehicleViewSet, basename='client-vehicles')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(clients_router.urls)),
]