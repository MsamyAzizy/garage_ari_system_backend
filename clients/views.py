import csv 
from django.http import HttpResponse 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated 
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, mixins, filters, status 
from rest_framework.decorators import action 
from rest_framework.parsers import MultiPartParser, FormParser 

from django.db.models import Sum 
from django.utils import timezone
from django.db import transaction 
from datetime import timedelta
from dateutil.relativedelta import relativedelta 

# Import Models from the client app
from .models import Client, Vehicle
# Import the new ClientImportSerializer
from .serializers import ClientListSerializer, ClientDetailSerializer, VehicleSerializer, ClientImportSerializer

# CRITICAL IMPORT FOR METRICS
from jobcards.models import JobCard 

# Helper function to calculate percentage change
def calculate_percentage_change(current, previous):
    if previous == 0:
        return '+100.0%' if current > 0 else '+0.0%'
    
    change_ratio = (current - previous) / previous
    percentage = round(change_ratio * 100, 1)
    return f"{'+' if percentage >= 0 else ''}{percentage:.1f}%"

# ----------------------------------
# 0. Dashboard Metrics API View 
# ----------------------------------
class DashboardMetricsView(APIView):
    """
    Returns summarized data for the main dashboard statistics.
    """
    permission_classes = [IsAuthenticated] 

    def get(self, request, *args, **kwargs):
        now = timezone.now()
        
        start_of_current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_previous_month = start_of_current_month - relativedelta(months=1)

        # --- 1. Total Clients & Percentage Change & STATUS ALERT ---
        total_clients = Client.objects.filter(is_active=True).count()
        client_status_alert = 'RED_ALERT' if total_clients < 5 else 'OK'
        
        current_month_new_clients = Client.objects.filter(
            is_active=True, date_created__gte=start_of_current_month 
        ).count()
        last_month_new_clients = Client.objects.filter(
            is_active=True, date_created__gte=start_of_previous_month,
            date_created__lt=start_of_current_month 
        ).count()
        client_change = calculate_percentage_change(current_month_new_clients, last_month_new_clients)

        # --- 2. Total Vehicles ---
        total_vehicles = Vehicle.objects.count()

        # --- 3. Total Sales Orders (Revenue This Month) & MoM Change ---
        try:
            current_month_sales_agg = JobCard.objects.filter(
                status='PAID', date_completed__gte=start_of_current_month 
            ).aggregate(total_revenue=Sum('total_due')) 
            current_month_revenue = current_month_sales_agg.get('total_revenue') or 0
        except Exception:
            current_month_revenue = 0
            
        total_sales_display = f"Tsh {current_month_revenue:,.0f}" 
        
        try:
            last_month_sales_agg = JobCard.objects.filter(
                status='PAID', date_completed__gte=start_of_previous_month,
                date_completed__lt=start_of_current_month
            ).aggregate(total_revenue=Sum('total_due')) 
            last_month_revenue = last_month_sales_agg.get('total_revenue') or 0
        except Exception:
            last_month_revenue = 0

        sales_change = calculate_percentage_change(current_month_revenue, last_month_revenue)

        # --- 4. Total Appointments (Upcoming 7 Days) & MoM Change ---
        next_seven_days = now + timedelta(days=7)
        
        upcoming_appointments = JobCard.objects.filter(
            date_in__range=[now, next_seven_days], 
            status__in=['OPEN', 'IN_PROGRESS'] 
        ).count()
        
        current_month_appointments = JobCard.objects.filter(
            date_in__gte=start_of_current_month 
        ).count()
        last_month_appointments = JobCard.objects.filter(
            date_in__gte=start_of_previous_month,
            date_in__lt=start_of_current_month 
        ).count()
        appointment_change = calculate_percentage_change(current_month_appointments, last_month_appointments)

        data = {
            'total_clients': total_clients,
            'total_vehicles': total_vehicles,
            'total_sales': total_sales_display, 
            'total_appointments': upcoming_appointments,
            'client_percentage_change': client_change,
            'sales_percentage_change': sales_change,
            'appointment_percentage_change': appointment_change, 
            'client_status_alert': client_status_alert,
        }
        return Response(data)

# ----------------------------------
# 1. Client ViewSet (with Export and Import Actions)
# ----------------------------------
class ClientViewSet(viewsets.ModelViewSet):
    """
    Provides full CRUD operations for Clients, including search filtering, 
    pagination, data export, and data import.
    """
    
    queryset = Client.objects.filter(is_active=True).order_by('last_name')
    pagination_class = PageNumberPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'company_name', 'email', 'phone_number', 'tax_id', 'notes']
    ordering_fields = ['last_name', 'date_created']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ClientListSerializer
        return ClientDetailSerializer
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    # 1. CORRECTED ACTION: Export Clients to CSV
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Generates and returns a CSV file of all active client data."""
        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="clients_export.csv"'},
        )
        writer = csv.writer(response)
        
        # ✅ FIX: 'date_updated' is removed from the list of fields.
        field_names = [
            'id', 'first_name', 'last_name', 'company_name', 'email', 
            'phone_number', 'client_type', 'address', 'city', 'state', 
            'zip_code', 'tax_id', 'notes', 'date_created',
            'is_tax_exempt', 'apply_discount', 'labor_rate_override', 'custom_labor_rate', 
            'parts_markup_override', 'custom_markup_percentage', 'payment_terms_override', 
            'custom_payment_terms'
        ]
        
        writer.writerow([field.replace('_', ' ').title() for field in field_names]) 

        clients = Client.objects.filter(is_active=True).values(*field_names)
        
        for client in clients:
            row_data = [client[field] for field in field_names]
            writer.writerow(row_data)

        return response
        
    # 2. 🏆 CRITICAL FIX APPLIED HERE: Renamed the method to 'import' 
    #    OR explicitly set url_path='import'. Using the latter for clarity.
    @action(
        detail=False, 
        methods=['post'], 
        parser_classes=(MultiPartParser, FormParser), 
        url_path='import' 
    )
    def import_clients(self, request):
        """Receives a file upload and imports client data from a CSV file."""
        
        if 'file' not in request.data:
            return Response({"error": "No file uploaded in the request."}, status=status.HTTP_400_BAD_REQUEST)

        file = request.data['file']
        
        try:
            # Read the file and decode, handling potential headers issue
            # Using readlines() then decoding ensures line endings are handled correctly
            file_data = file.read().decode('utf-8')
            decoded_file = file_data.splitlines()
            reader = csv.DictReader(decoded_file)
        except Exception as e:
            return Response({"error": f"Error reading or decoding file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        imported_clients = []
        errors = []
        line_number = 1
        
        # Clean headers for reliable mapping to serializer fields
        # This is CRITICAL for robust import handling
        if reader.fieldnames:
            fieldnames = [key.strip().lower().replace(' ', '_') for key in reader.fieldnames]
            reader.fieldnames = fieldnames
        
        try:
            with transaction.atomic():
                for row in reader:
                    line_number += 1
                    
                    # Create a clean dictionary from the row, converting empty strings to None
                    clean_row = {
                        k: (v.strip() if isinstance(v, str) and v.strip() != '' else None)
                        for k, v in row.items() 
                        if k is not None # Ignore rows with unmappable headers
                    }
                    
                    serializer = ClientImportSerializer(data=clean_row)
                    
                    if serializer.is_valid():
                        imported_clients.append(serializer.save())
                    else:
                        errors.append({
                            "line": line_number,
                            "data_provided": dict(row),
                            "errors": serializer.errors
                        })
                
                if errors:
                    # Rollback happens here due to transaction.atomic() scope ending with an exception
                    raise Exception(f"Import failed due to data validation errors on {len(errors)} row(s).")
            
            # If the atomic block completes successfully:
            return Response({
                "message": f"Successfully imported {len(imported_clients)} new clients.",
                "imported_count": len(imported_clients)
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Catch the validation errors raised above, and other unexpected errors
            response_data = {
                "error": "Data Import Failed.",
                "detail": str(e),
            }
            if errors:
                # Only include detailed errors if validation failed
                response_data["detailed_errors"] = errors
                
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


# ----------------------------------
# 2. Vehicle ViewSet (FIXED for Nested Routing)
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
    
    🛑 FIXED: get_queryset now filters vehicles by the client_pk from the URL.
    """
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    
    def get_queryset(self):
        # 🏆 CRITICAL FIX: Filter vehicles by the 'client_pk' passed in the nested URL
        # The nested router defines this lookup parameter.
        client_pk = self.kwargs.get('client_pk')
        
        if client_pk:
            # Return vehicles associated with this specific client
            return self.queryset.filter(client_id=client_pk)
            
        # If accessing the view set without nesting (which shouldn't happen with the current URL structure)
        return self.queryset.none()
        
    def perform_create(self, serializer):
        # Ensure the vehicle is linked to the client from the URL on creation
        client_pk = self.kwargs.get('client_pk')
        
        try:
            client = Client.objects.get(pk=client_pk)
        except Client.DoesNotExist:
            # If the client doesn't exist, raise an error (should be handled by URL/Router logic too)
            raise serializers.ValidationError({"client": "Client not found."})

        serializer.save(client=client)