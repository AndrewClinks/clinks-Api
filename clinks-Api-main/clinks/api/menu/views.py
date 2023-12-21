from __future__ import unicode_literals

import time

from .serializers import *

from ..utils.Views import SmartDetailAPIView



class Detail(SmartDetailAPIView):

    model = Menu
    detail_serializer = MenuDetailSerializer
    
    def queryset(self, request, id):
        from ..company.models import Company
        start_time = time.time()

        queryset = Menu.objects.filter(venue_id=id)

        if self.is_company_member_request():
            queryset = queryset.filter(venue__company__members__user_id=self.request.user.id)
            queryset = Company.filter_with_passcode(self, request, queryset, "venue__company__passcode")

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time} seconds")
        return queryset

    def has_permission(self, request, method):
        if method == "PATCH":
            return self.is_admin_request()

        return True

