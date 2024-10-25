from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from ..order.serializers import OrderCreateSerializer
from ..utils.Views import SmartAPIView
from ..utils.Permissions import IsAdminPermission
from ..venue.models import Venue
from ..menu_item.models import MenuItem
from django.http import JsonResponse
import logging
import os
logger = logging.getLogger('clinks-api-live')

class CreateTestOrder(SmartAPIView):
    permission_classes = [IsAdminPermission]
    create_serializer = OrderCreateSerializer

    def get(self, request, venue_id, *args, **kwargs):
        venue = Venue.objects.get(id=venue_id)
        menu_items = MenuItem.objects.filter(menu_id=venue_id) 

        # Prepare the items (based on your example data from the query)
        items = [
            {
                "id": item.id,
                "menu_item_id": item.id, 
                "quantity": 1, 
                "price": item.price
            }
            for item in menu_items
        ]

        # Create the address
        # address_data = {
        #     "latitude": 51.896791,  # Example latitude (Cork coordinates)
        #     "longitude": -8.470114,  # Example longitude (Cork coordinates)
        #     "line_1": "12 South Mall",  # Example line_1
        #     "city": "Cork", 
        #     "state": "Munster", 
        #     "country": "Ireland",
        #     "country_short": "IE"
        # }

        # Some of this is alsy being set in the order serializer
        # It needs this initial data to get through initial validators
        # Set test data for required fields
        # data = {
        #     "customer": 7,  # Andrew Scannell
        #     "venue": 1,
        #     "items": items,  # The items pulled from the database for the venue
        #     "address": 3, # 12 South Mall, Cork
        #     "menu": venue.id,
        #     "payment": {
        #         "card": "1", # this is needed here and then again inside the serializer... I know... it's a bit weird
        #         "method": "card",
        #         "expected_price": sum(item['price'] for item in items),
        #         "amount": sum(item['price'] for item in items),  # Calculate total amount from items
        #         "currency": "EUR",
        #         "status": "PENDING"
        #     },
        #     "status": 'PENDING',
        #     "delivery_status": 'AWAITING',
        #     "total_price": sum(item['price'] for item in items),  # Set total price
        #     "order_date": timezone.now(),
        # }
        data = {
            "venue": venue.id,  # Venue ID from your setup
            "menu": venue.id,  # Using the venue ID for the menu as in the frontend data
            "payment": {
                "card": "1",  # Mock card ID
                "expected_price": sum(item['price'] for item in items),  # Expected total price from items
                "tip": 0,  # Assuming no tip for the test, adjust if needed
            },
            "items": items,  # The items pulled from the database for the venue
        }

        # Validate and save the new order
        serializer = self.create_serializer(data=data, context={'is_test_order': True})
        if serializer.is_valid():
            serializer.save()
            logger.info(f"TEST ORDER created successfully.")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            logger.error(f"TEST ORDER Validation failed with errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)