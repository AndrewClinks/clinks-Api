from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from ..order.serializers import OrderCreateSerializer
from ..utils.Views import SmartAPIView
from ..utils.Permissions import IsAdminPermission
from ..venue.models import Venue
from ..menu_item.models import MenuItem
from ..address.serializers import AddressCreateSerializer

class CreateTestOrder(SmartAPIView):
    permission_classes = [IsAdminPermission]
    create_serializer = OrderCreateSerializer

    def get(self, request, venue_id, *args, **kwargs):
        venue_id = 1
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

        # Define the latitude and longitude for the address
        address_data = {
            "latitude": 51.896791,  # Example latitude (Cork coordinates)
            "longitude": -8.470114,  # Example longitude (Cork coordinates)
            "line_1": "12 South Mall",  # Example line_1
            "city": "Cork", 
            "state": "Munster", 
            "country": "Ireland",
            "country_short": "IE"
        }

        # Create the address
        address_serializer = AddressCreateSerializer(data=address_data)
        if address_serializer.is_valid():
            address = address_serializer.save()
        else:
            return Response(address_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Some of this is alsy being set in the order serializer
        # It needs this initial data to get through initial validators
        # Set test data for required fields
        data = {
            "customer": 7,  # Andrew Scannell
            "venue": venue.id,
            "items": items,  # The items pulled from the database for the venue
            "address": address.id,
            "menu": venue.id,
            "payment": {
                "card": "16", # an old card that belongs to Andy
                "method": "card",
                "expected_price": sum(item['price'] for item in items),
                "amount": sum(item['price'] for item in items),  # Calculate total amount from items
                "currency": "EUR",
                "status": "PENDING"
            },
            "status": 'PENDING',
            "delivery_status": 'AWAITING',
            "total_price": sum(item['price'] for item in items),  # Set total price
            "order_date": timezone.now(),
        }

        # Allow incoming request to override test data if provided
        # data.update(request.data)

        # Validate and save the new order
        serializer = self.create_serializer(data=data, context={'is_test_order': True})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)