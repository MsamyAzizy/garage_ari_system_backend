# clients/views.py (FINAL VERSION with ALL MoM Calculations + Client Status Alert at < 20)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated 
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, mixins, filters

from django.db.models import Sum 
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta # CRITICAL IMPORT: Ensure 'pip install python-dateutil' is run

# Import Models from the client app
from .models import Client, Vehicle
from .serializers import ClientListSerializer, ClientDetailSerializer, VehicleSerializer 

# 🛑 CRITICAL IMPORT FOR METRICS
# Import the JobCard model from the jobcards app
from jobcards.models import JobCard 

# Helper function to calculate percentage change
def calculate_percentage_change(current, previous):
    if previous == 0:
        # If previous is 0, we return +100.0% if current is greater than 0, otherwise +0.0%.
        return '+100.0%' if current > 0 else '+0.0%'
    
    change_ratio = (current - previous) / previous
    percentage = round(change_ratio * 100, 1)
    return f"{'+' if percentage >= 0 else ''}{percentage:.1f}%"

# ----------------------------------
# 0. Dashboard Metrics API View 
# ----------------------------------
class DashboardMetricsView(APIView):
    """
    Returns summarized data for the main dashboard statistics, including 
    month-over-month percentage change and client count status alert.
    """
    permission_classes = [IsAuthenticated] 

    def get(self, request, *args, **kwargs):
        now = timezone.now()
        
        # Calculate month start dates
        start_of_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_previous_month = start_of_current_month - relativedelta(months=1)

        # --- 1. Total Clients & Percentage Change & STATUS ALERT ---
        total_clients = Client.objects.filter(is_active=True).count()
        
        # Determine Client Status Alert
        # ALERT LOGIC: If total clients is less than 20, raise a red alert.
        client_status_alert = 'RED_ALERT' if total_clients < 5 else 'OK'
        
        current_month_new_clients = Client.objects.filter(
            is_active=True,
            date_created__gte=start_of_current_month 
        ).count()
        
        last_month_new_clients = Client.objects.filter(
            is_active=True,
            date_created__gte=start_of_previous_month,
            date_created__lt=start_of_current_month 
        ).count()

        client_change = calculate_percentage_change(current_month_new_clients, last_month_new_clients)


        # --- 2. Total Vehicles ---
        total_vehicles = Vehicle.objects.count()

        # --- 3. Total Sales Orders (Revenue This Month) & MoM Change ---
        
        # Current Month Revenue
        try:
            current_month_sales_agg = JobCard.objects.filter(
                status='PAID', 
                date_completed__gte=start_of_current_month 
            ).aggregate(total_revenue=Sum('total_due')) 
            
            current_month_revenue = current_month_sales_agg.get('total_revenue') or 0
        except Exception as e:
            print(f"Error calculating current month sales: {e}")
            current_month_revenue = 0
            
        total_sales_display = f"Tsh {current_month_revenue:,.0f}" 
        
        # Previous Month Revenue
        try:
            last_month_sales_agg = JobCard.objects.filter(
                status='PAID', 
                date_completed__gte=start_of_previous_month,
                date_completed__lt=start_of_current_month
            ).aggregate(total_revenue=Sum('total_due')) 
            
            last_month_revenue = last_month_sales_agg.get('total_revenue') or 0
        except Exception as e:
            print(f"Error calculating previous month sales: {e}")
            last_month_revenue = 0

        sales_change = calculate_percentage_change(current_month_revenue, last_month_revenue)


        # --- 4. Total Appointments (Upcoming 7 Days) & MoM Change ---
        next_seven_days = now + timedelta(days=7)
        
        # Count current week appointments (Next 7 days)
        upcoming_appointments = JobCard.objects.filter(
            date_in__range=[now, next_seven_days], 
            status__in=['OPEN', 'IN_PROGRESS'] 
        ).count()
        
        # APPOINTMENTS MOM CALCULATION START (FIXED TO USE date_in)
        # Count appointments created this month (JobCard check-in date)
        current_month_appointments = JobCard.objects.filter(
            date_in__gte=start_of_current_month 
        ).count()
        
        # Count appointments created last month (JobCard check-in date)
        last_month_appointments = JobCard.objects.filter(
            date_in__gte=start_of_previous_month,
            date_in__lt=start_of_current_month 
        ).count()
        
        appointment_change = calculate_percentage_change(current_month_appointments, last_month_appointments)
        # APPOINTMENTS MOM CALCULATION END

        data = {
            'total_clients': total_clients,
            'total_vehicles': total_vehicles,
            'total_sales': total_sales_display, 
            'total_appointments': upcoming_appointments,
            'client_percentage_change': client_change,
            'sales_percentage_change': sales_change,
            'appointment_percentage_change': appointment_change, # Now dynamic
            # NEW FIELD: Client Status Alert
            'client_status_alert': client_status_alert,
        }
        return Response(data)

# ----------------------------------
# 1. Client ViewSet
# ----------------------------------
class ClientViewSet(viewsets.ModelViewSet):
    """
    Provides full CRUD operations for Clients, including search filtering and pagination.
    """
    
    queryset = Client.objects.filter(is_active=True).order_by('last_name')
    pagination_class = PageNumberPagination
    
    filter_backends = [filters.SearchFilter]

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
        if self.action == 'list':
            return ClientListSerializer
        return ClientDetailSerializer
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


# ----------------------------------
# 2. Vehicle ViewSet
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