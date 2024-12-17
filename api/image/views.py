from __future__ import unicode_literals

from .models import Image


from .serializers import (
    ImageCreateSerializer,
    ImageDetailSerializer,
)

from ..utils.Permissions import (
    IsAuthenticated
)
from ..utils import Constants

from ..utils.Views import SmartPaginationAPIView


class ListCreate(SmartPaginationAPIView):
    permission_classes = [IsAuthenticated]

    model = Image

    create_serializer = ImageCreateSerializer
    detail_serializer = ImageDetailSerializer

    def override_post_data(self, request, data):
        if len(data) == 0:
            data = {}

        data["user_type"] = request.user.role

        return data





