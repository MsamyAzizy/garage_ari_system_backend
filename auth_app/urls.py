# auth_app/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView, 
    UserView,
    RegistrationView,
    # 🏆 NEW IMPORT: Import the Employee ViewSet
    EmployeeViewSet,  
)

# 1. Initialize the Router
router = DefaultRouter()

# 2. Register the Employee ViewSet
# This will create endpoints like:
# /employees/ (GET, POST)
# /employees/{pk}/ (GET, PUT, DELETE)
router.register(r'employees', EmployeeViewSet, basename='employee')


urlpatterns = [
    # ------------------------------------------------------------------
    # JWT & Standard User Endpoints
    # ------------------------------------------------------------------
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegistrationView.as_view(), name='user_register'),
    path('user/', UserView.as_view(), name='user-details'), 
    
    # ------------------------------------------------------------------
    # 🏆 NEW: Employee Management Endpoint
    # ------------------------------------------------------------------
    # DRF Router routes all ViewSet operations here
    path('', include(router.urls)),
]