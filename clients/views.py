# clients/views.py

from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import filters 
# 🏆 CRITICAL NEW IMPORT: Import the standard pagination class
from rest_framework.pagination import PageNumberPagination 

# Assuming ClientListSerializer, ClientDetailSerializer, and VehicleSerializer 
# are defined in clients/serializers.py and correctly include all fields.
from .models import Client, Vehicle
from .serializers import ClientListSerializer, ClientDetailSerializer, VehicleSerializer 

# ----------------------------------
# 1. Client ViewSet (List, Retrieve, Create, Update, Delete)
# ----------------------------------

class ClientViewSet(viewsets.ModelViewSet):
    """
    Provides full CRUD operations for Clients, including search filtering and pagination.
    """
    
    queryset = Client.objects.filter(is_active=True).order_by('last_name')
    
    # NOTE: Uncomment if you are using authentication
    # permission_classes = [IsAuthenticated]
    
    # 🏆 CRITICAL FIX: Explicitly set PageNumberPagination
    # This ensures the API returns paginated results (10 per page, based on settings.py)
    pagination_class = PageNumberPagination
    
    # Enable SearchFilter
    filter_backends = [filters.SearchFilter]

    # Define search fields. 
    search_fields = [
        'first_name', 
        'last_name', 
        'company_name', 
        'email', 
        'phone_number',
        'tax_id',     
        'notes'       
    ]
    ordering_fields = ['last_name', 'date_created']
    
    def get_serializer_class(self):
        """
        Dynamically choose the serializer based on the action (list vs detail).
        """
        if self.action == 'list':
            # Use the lighter serializer for the main table view
            return ClientListSerializer
        # Use the detail serializer for all other actions (create, retrieve, update)
        return ClientDetailSerializer
    
    def perform_destroy(self, instance):
        """
        We perform a soft-delete by setting is_active=False instead of deleting the record.
        """
        instance.is_active = False
        instance.save()


# ----------------------------------
# 2. Vehicle ViewSet (Create, Update, Delete, Retrieve, LISTING ADDED)
# ----------------------------------

class VehicleViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    Provides creation, detail viewing, updating, deletion, and listing of Vehicles.
    """
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    # NOTE: Uncomment if you are using authentication
    # permission_classes = [IsAuthenticated]
    
    # OPTIONAL: You may want to paginate the vehicles list as well
    # pagination_class = PageNumberPagination 
    
    # Note: When creating a vehicle, the client ID must be included in the POST data.