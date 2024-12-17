from __future__ import unicode_literals

from .models import AllTimeStat

from rest_framework import status

from rest_framework.response import Response

from ..utils.Permissions import (
    IsAdminPermission,
)

from ..utils import QueryParams, Constants

from ..utils.Views import SmartAPIView


class List(SmartAPIView):
    permission_classes = [IsAdminPermission, ]

    def get(self, request):
        types = QueryParams.get_enum_list(request, "types", Constants.ALL_TIME_STAT_TYPES, raise_exception=True)

        all_time_stats = AllTimeStat.objects.filter(type__in=types)

        data = {}

        for all_time_stat in all_time_stats:
            data[f"{all_time_stat.type}"] = int(all_time_stat.value)

        for current_type in types:
            if current_type not in data:
                data[current_type] = 0

        return Response(data, status=status.HTTP_200_OK)