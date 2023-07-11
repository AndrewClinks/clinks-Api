from __future__ import unicode_literals

from rest_framework import status
from rest_framework.response import Response

from django.db.models import Q

from ..venue.models import Venue
from ..delivery_distance.models import DeliveryDistance

from ..utils import QueryParams, Point, Distance

from ..utils.Views import SmartAPIView


class Detail(SmartAPIView):

    def get(self, request, id):
        if not self.is_customer_request() and not self.is_anonymous_request():
            return self.get_permission_denied_response(request, "GET")

        point = Point.get(request)

        if not point:
            return self.respond_with("'latitude' and 'longitude' are required", status_code=status.HTTP_400_BAD_REQUEST)

        venue = Venue.objects.filter(id=id).first()

        if not venue:
            return self.respond_with("Please check id", status_code=status.HTTP_400_BAD_REQUEST)

        distance = Distance.between(venue.address.point, point, True)

        fee = None
        try:
            fee = DeliveryDistance.get_by_distance(distance).fee
        except Exception as e:
            return self.respond_with("Venue cannot deliver to this location", status_code=status.HTTP_400_BAD_REQUEST)

        data = {
            "fee": fee
        }

        return Response(data, status=status.HTTP_200_OK)




