# auth_app/views.py

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
# 🚀 ADDED generics
from rest_framework import serializers, status, generics 
from django.contrib.auth import get_user_model 

# Assuming this file exists and contains the RegistrationSerializer AND the new UserSerializer
# 🛑 NOTE: Ensure you import the new UserSerializer from .serializers
from .serializers import RegistrationSerializer, UserSerializer 

# -----------------
# Serializer for Login
# -----------------
class CustomTokenObtainPairSerializer(serializers.Serializer):
    """
    Overrides the default SimpleJWT serializer to accept 'email' instead of 'username'
    as the login identifier. (Remains as is)
    """
    username_field = 'email'
    
    def validate(self, attrs):
        return super().validate(attrs)


# -----------------
# JWT Views
# -----------------

class CustomTokenObtainPairView(TokenObtainPairView):
    """View for obtaining JWT token (handles the login request)."""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (AllowAny,) 

class CustomTokenRefreshView(TokenRefreshView):
    """View for refreshing the JWT token (maintains the session)."""
    permission_classes = (AllowAny,)

# -----------------
# User Registration View 
# -----------------

class RegistrationView(APIView):
    """
    Endpoint for creating a new user account. (Remains as is)
    """
    permission_classes = [AllowAny] 
    
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            
            return Response(
                {"detail": "User registered successfully. You can now log in."}, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------
# User Profile View 🚀 THE CORRECT DRF APPROACH 🚀
# -----------------

class UserView(generics.RetrieveAPIView):
    """
    Endpoint to retrieve details of the currently authenticated user using UserSerializer.
    Accessed by the frontend via /api/auth/user/
    """
    permission_classes = [IsAuthenticated] 
    serializer_class = UserSerializer

    def get_object(self):
        # DRF automatically finds the user from the JWT token in the request headers
        # and makes it available as request.user.
        return self.request.user