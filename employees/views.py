# employees/views.py (FINAL, STABLE VIEWSET)

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated 
from .models import Employee
from .serializers import EmployeeSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for handling all CRUD operations for the Employee model.
    This replaces individual APIView classes for greater stability and consistency 
    in handling create, update, and partial update operations.
    """
    # Define the base queryset
    queryset = Employee.objects.all().order_by('last_name', 'first_name')
    
    # Define the serializer used for input and output
    serializer_class = EmployeeSerializer
    
    # Adjust permission_classes as needed for your project's security
    permission_classes = [IsAuthenticated]
    
    # Optional: You can customize the behavior of the update method if needed, 
    # but the default ModelViewSet.update() is usually sufficient when serializers are correct.
    # def update(self, request, *args, **kwargs):
    #     # Example: ensure partial update is enabled for PUT/PATCH
    #     kwargs['partial'] = True 
    #     return super().update(request, *args, **kwargs)