# clinks/api/test_order/urls.py

from django.urls import path
from .views import CreateTestOrder  # Import the view from views.py

urlpatterns = [
    path('', CreateTestOrder.as_view(), name='create-test-order'),  # Define the test-order creation URL
]