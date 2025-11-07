# auth_app/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView, 
    # 🛑 CORRECTED: Import the new, cleaner UserView (from views.py)
    UserView,
    RegistrationView,  
)

urlpatterns = [
    # JWT Authentication Endpoints
    # POST to obtain token (Login)
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # POST to refresh token (Session renewal)
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User Registration Endpoint
    path('register/', RegistrationView.as_view(), name='user_register'),
    
    # 🚀 CORRECTED: GET user details (Requires valid token)
    # The frontend is configured to call /api/auth/user/
    path('user/', UserView.as_view(), name='user-details'), 
]