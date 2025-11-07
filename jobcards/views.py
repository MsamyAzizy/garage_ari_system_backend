# jobcards/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum
from .models import JobCard, Payment
from .serializers import JobCardSerializer, PaymentSerializer

# ----------------------------------
# 1. JobCard ViewSet (CRUD, Search, Status Management)
# ----------------------------------

class JobCardViewSet(viewsets.ModelViewSet):
    """
    Provides CRUD for Job Cards. Supports searching, filtering, and status actions.
    """
    queryset = JobCard.objects.select_related('client', 'vehicle', 'assigned_technician')
    serializer_class = JobCardSerializer
    permission_classes = [IsAuthenticated]
    
    filter_backends = [SearchFilter, OrderingFilter]
    
    # Allows search by job number, client name, or vehicle plate/VIN
    search_fields = [
        'job_number', 
        'client__first_name', 'client__last_name', 
        'vehicle__license_plate', 'vehicle__vin'
    ]
    ordering_fields = ['job_number', 'status', 'date_in', 'total_due']
    
    def get_queryset(self):
        """Filter queryset based on user role or display active jobs."""
        # For simplicity, we filter by the status field set by the client (e.g., OPEN, PAID)
        return super().get_queryset()

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Custom endpoint to quickly update the job card status."""
        job_card = self.get_object()
        new_status = request.data.get('status')
        
        if new_status and new_status in [choice[0] for choice in JobCard.STATUS_CHOICES]:
            job_card.status = new_status
            job_card.save()
            return Response({'status': f'Job card status updated to {new_status}'})
        
        return Response({'error': 'Invalid status provided'}, status=status.HTTP_400_BAD_REQUEST)

    
# ----------------------------------
# 2. Payment ViewSet (Nested within JobCard logic)
# ----------------------------------

class PaymentViewSet(viewsets.GenericViewSet, viewsets.mixins.CreateModelMixin):
    """
    Handles adding new payments to a specific Job Card.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Custom create to link the payment to the job card."""
        job_card_id = self.kwargs.get('job_card_pk') # Extracted from the nested URL
        
        try:
            job_card = JobCard.objects.get(pk=job_card_id)
        except JobCard.DoesNotExist:
            return Response({'detail': 'Job Card not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save the payment, linking it to the job card
        serializer.save(job_card=job_card) 
        
        # The Payment model's save method will automatically update JobCard.total_paid
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)