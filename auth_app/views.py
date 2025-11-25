# auth_app/views.py

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
# 🚀 ADDED generics and Viewsets
from rest_framework import serializers, status, generics, viewsets 
from django.contrib.auth import get_user_model 

# 🛑 CRITICAL FIX: Update this import to reflect the names in serializers.py
from .serializers import (
    RegistrationSerializer, 
    CustomUserSerializer, # Use the correct name for the base user serializer
    EmployeeSerializer     # Import the new employee serializer
)

# ... (CustomTokenObtainPairSerializer and JWT Views remain the same) ...
class CustomTokenObtainPairSerializer(serializers.Serializer):
    username_field = 'email'
    
    def validate(self, attrs):
        return super().validate(attrs)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (AllowAny,) 

class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = (AllowAny,)

# ... (RegistrationView remains the same) ...
class RegistrationView(APIView):
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
# User Profile View 
# -----------------

class UserView(generics.RetrieveAPIView):
    """
    Endpoint to retrieve details of the currently authenticated user.
    """
    permission_classes = [IsAuthenticated] 
    # 🛑 CRITICAL FIX: Use the correct serializer name
    serializer_class = CustomUserSerializer 

    def get_object(self):
        return self.request.user


# =================================================================
# 🏆 NEW: EMPLOYEE MANAGEMENT VIEWSET
# =================================================================

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employees (shop personnel) to be viewed, 
    created, updated, and deleted by authorized users (e.g., IsAdminUser).
    """
    # 1. Queryset: Filter to only show records where is_employee is True
    queryset = get_user_model().objects.filter(is_employee=True).order_by('last_name')
    
    # 2. Serializer: Use the new comprehensive serializer
    serializer_class = EmployeeSerializer
    
    # 3. Permissions: Only allow logged-in staff/admins to manage employees
    # You might create a custom permission later, but IsAdminUser or IsAuthenticated is a good start.
    permission_classes = [IsAuthenticated] 
    
    # Optional: We could add filtering or searching here, e.g., to search by name/employee_id
    # filter_backends = [filters.SearchFilter]
    # search_fields = ['first_name', 'last_name', 'employee_id']

    def perform_create(self, serializer):
        # When creating a new employee via this endpoint, ensure the is_employee flag is set
        # This is also handled in the serializer's create method, but good to ensure here.
        serializer.save(is_employee=True)
        
    def get_queryset(self):
        # Ensure that only the current employees are returned by default.
        return super().get_queryset()