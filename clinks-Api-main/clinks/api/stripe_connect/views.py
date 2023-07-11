from rest_framework import status
from rest_framework.response import Response

from ..company.models import Company

from ..utils.Permissions import (
    IsAdminPermission,
    IsCompanyMemberPermission
)

from ..utils.Views import SmartAPIView

from ..utils import QueryParams, Constants
from ..utils.stripe import Connect as StripeConnect


class Connect(SmartAPIView):
    permission_classes = [IsAdminPermission | IsCompanyMemberPermission]

    def get(self, request):
        company_id = QueryParams.get_int(request, "company_id", raise_exception=True)
        return_url = QueryParams.get_str(request, "return_url", raise_exception=True)
        refresh_url = QueryParams.get_str(request, "refresh_url", raise_exception=True)

        if self.is_company_member_request():
            company = self.get_company_member_from_request().company
        else:
            company = Company.objects.filter(id=company_id).first()

            if not company:
                return self.respond_with("Company with this id does not exist", status_code=status.HTTP_400_BAD_REQUEST)

        if company.stripe_verification_status == Constants.STRIPE_VERIFICATION_STATUS_VERIFIED:
            return self.respond_with("This company is already connected to stripe.", status_code=status.HTTP_400_BAD_REQUEST)

        connect_url = StripeConnect.get_standard_connect_activation_link(company, refresh_url, return_url)

        data = {
            "connect_url": connect_url
        }

        return Response(data=data, status=status.HTTP_200_OK)
