# jobcards/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView # <-- IMPORTED FOR KANBAN VIEW
from django.db.models import Sum

from .models import JobCard, Payment
from .serializers import JobCardSerializer, PaymentSerializer

# --- Assuming these related models are available for imports. Adjust if path is different. ---
# If JobCard is in this app, you don't need these here, but for clarity:
# from clients.models import Client, Vehicle 
# ------------------------------------------------------------------------------------------

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
            # Respond with the updated serialized object if needed, but a success message is fine.
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
        job_card_id = self.kwargs.get('job_card_pk') 
        
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


# ----------------------------------
# 3. Kanban Board API View (NEW)
# ----------------------------------
class JobCardKanbanView(APIView):
    """
    Returns active Job Cards grouped by their status for the Kanban board.
    Filters out 'PAID' status by default.
    """
    permission_classes = [IsAuthenticated] 

    def get(self, request, *args, **kwargs):
        # Define the active statuses for the Kanban columns (excluding 'PAID'/'CLOSED')
        # Ensure these match the JobCard.STATUS_CHOICES keys
        KANBAN_STATUSES = ['OPEN', 'IN_PROGRESS', 'READY_FOR_PICKUP']

        # Fetch all active job cards, ordered by date_in (check-in date)
        job_cards = JobCard.objects.filter(
            status__in=KANBAN_STATUSES
        ).select_related('client', 'vehicle').order_by('date_in')
        
        # Prepare the data structure to group cards by status
        kanban_data = {status: [] for status in KANBAN_STATUSES}
        
        # Manually group and partially serialize the job cards
        for job_card in job_cards:
            # We must use string formatting for dates and currency for the frontend
            card_data = {
                'id': job_card.id,
                'job_number': job_card.job_number,
                'status': job_card.status,
                'client_name': f"{job_card.client.first_name} {job_card.client.last_name}",
                'vehicle_license': job_card.vehicle.license_plate,
                'vehicle_model': f"{job_card.vehicle.make} {job_card.vehicle.model}",
                # Only display the date part
                'date_in': job_card.date_in.strftime('%Y-%m-%d') if job_card.date_in else None,
                'total_due': f"Tsh {job_card.total_due:,.0f}" if job_card.total_due is not None else "Tsh 0",
            }
            if job_card.status in kanban_data:
                kanban_data[job_card.status].append(card_data)

        # Include the list of status keys for the frontend to easily iterate
        return Response({
            'statuses': KANBAN_STATUSES,
            'columns': kanban_data,
        })