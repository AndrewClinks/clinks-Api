from __future__ import unicode_literals

from .serializers import *

from ..utils.Views import SmartDetailAPIView

from ..utils import Body


class Detail(SmartDetailAPIView):

    model = Menu
    detail_serializer = MenuDetailSerializer
    
    def queryset(self, request, id):
        from ..company.models import Company

        queryset = Menu.objects.filter(venue_id=id)

        if self.is_company_member_request():
            queryset = queryset.filter(venue__company__members__user_id=self.request.user.id)

            queryset = Company.filter_with_passcode(self, request, queryset, "venue__company__passcode")

            return queryset

        return queryset

    def has_permission(self, request, method):
        if method == "PATCH":
            return self.is_admin_request()

        return True

