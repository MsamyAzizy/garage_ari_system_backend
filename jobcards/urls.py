# jobcards/urls.py

from rest_framework_nested import routers
from django.urls import path, include
from .views import JobCardViewSet, PaymentViewSet

# We need a dependency: pip install djangorestframework-nested

# 1. Create the main router
router = routers.DefaultRouter()

# Register the main JobCardViewSet
# This gives us: /jobcards/ and /jobcards/{pk}/
router.register(r'', JobCardViewSet, basename='jobcard')

# 2. Create a nested router for Payments
# Payments can ONLY be accessed via a job card ID, e.g., /jobcards/{pk}/payments/
job_cards_router = routers.NestedSimpleRouter(router, r'', lookup='job_card')

# Register the PaymentViewSet as a nested resource
# The lookup='job_card' in the router links the payment to the parent job card
job_cards_router.register(r'payments', PaymentViewSet, basename='jobcard-payments')


urlpatterns = [
    # Main JobCard and Payments URLs
    path('', include(router.urls)), 
    path('', include(job_cards_router.urls)),
]

# Generated URLs:
# /api/jobcards/             (JobCard List/Create)
# /api/jobcards/{pk}/        (JobCard Detail/Update/Delete)
# /api/jobcards/{pk}/update-status/ (Custom Action)
# /api/jobcards/{job_card_pk}/payments/ (Payment Create)