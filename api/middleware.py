from .utils import DateUtils, Constants
import json


class LastSeen:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if not user.is_anonymous:
            user.last_seen = DateUtils.now()
            user.save()

        response = self.get_response(request)

        return response


class Logging:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .log.models import Log
        should_be_logged = request.method == "DELETE" or (
                    request.method == "GET" and request.GET.get("export") == "true")

        if should_be_logged and request.user.is_anonymous is False:
            body = request.body
            log_data = {
                "user": request.user,
                "request_url": request.get_full_path(),
                "type": Constants.LOG_TYPE_DELETE if request.method == "DELETE" else Constants.LOG_TYPE_EXPORT
            }

            if len(body) > 0:
                log_data.update({"request_data": json.loads(body)})

            Log.objects.create(**log_data)

        response = self.get_response(request)

        return response



