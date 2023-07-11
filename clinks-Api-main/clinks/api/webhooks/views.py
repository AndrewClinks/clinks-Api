from __future__ import unicode_literals

from rest_framework import status

from ..webhook_event.models import WebhookEvent
from rest_framework.response import Response

from ..utils import IP, Constants

from ..utils.Views import SmartAPIView
from ..utils.stripe import Connect, Utils


class StripeWebhook(SmartAPIView):

    def post(self, request):

        event_data = self.validate_request(request)
        if isinstance(event_data, Response):
            return event_data

        Utils.handle_webhook_event(request)

        event_id = request.data["id"]

        webhook_event = WebhookEvent()
        webhook_event.ip = IP.get_client_ip(request)
        webhook_event.event_id = event_id

        if WebhookEvent.objects.filter(event_id=event_id).exists():
            webhook_event.result = Constants.WEBHOOK_EVENT_RESULT_DUPLICATE
            webhook_event.data = request.data
            webhook_event.save()
            return self.respond_with("Duplicate event", "event_id", status_code=status.HTTP_400_BAD_REQUEST)

        webhook_event.data = request.data
        webhook_event.save()

        return self.respond_with("success", "status", status_code=status.HTTP_200_OK)

    def validate_request(self, request):

        if "id" not in request.data or "account" not in request.data:
            return self.respond_with("Invalid event data, missing 'id' or 'account'", status_code=status.HTTP_400_BAD_REQUEST)

        id = request.data["id"]
        account_id = request.data["account"]
        data = Utils.get_event(id=id, account_id=account_id)

        if not data:
            return self.respond_with("Invalid event data, no such event", status_code=status.HTTP_400_BAD_REQUEST)

        if data.object not in ["account"]:
            return self.respond_with(f"Invalid event data, unsupported type {data.object}",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        return data



