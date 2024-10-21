from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from ..order.serializers import OrderCreateSerializer
from ..utils.Views import SmartAPIView
from ..utils.Permissions import IsAdminPermission
from ..venue.models import Venue
from ..menu_item.models import MenuItem

class CreateTestOrder(SmartAPIView):
    permission_classes = [IsAdminPermission]
    create_serializer = OrderCreateSerializer

    def get(self, request, venue_id, *args, **kwargs):
        venue_id = 1
        venue = Venue.objects.get(id=venue_id)
        menu_items = MenuItem.objects.filter(menu_id=venue_id) 

        # Prepare the items (based on your example data from the query)
        items = [
            {"menu_item_id": item.id, "quantity": 1, "price": item.price}
            for item in menu_items
        ]

        # Set test data for required fields
        data = {
            "customer": request.user.id,  # Assuming the current user is the customer
            "venue": venue.id,
            "items": items,  # The items pulled from the database for the venue
            "payment": {
                "method": "card",
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
        serializer = self.create_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)