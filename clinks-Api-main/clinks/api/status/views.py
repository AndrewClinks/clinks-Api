from __future__ import unicode_literals

from rest_framework import status
from rest_framework.response import Response

from ..utils.Views import SmartAPIView

from ..utils import Availability


class List(SmartAPIView):

    def get(self, request):

        if not self.is_customer_request() and not self.is_anonymous_request():
            return self.respond_with("You do not have permission to access this", status_code=status.HTTP_403_FORBIDDEN)

        data = Availability.status()

        return Response(data, status=status.HTTP_200_OK)
