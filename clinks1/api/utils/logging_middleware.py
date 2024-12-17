# myapp/middleware/logging_middleware.py
import logging

# Set up logging
logger = logging.getLogger(__name__)

class LogPushNotificationRequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the path matches the APNS or GCM device endpoints
        if request.path.startswith('/device/apns') or request.path.startswith('/device/gcm'):
            logger.info(f"Push Notification Endpoint Called: {request.path}")

        # Pass the request to the next middleware or view
        response = self.get_response(request)
        return response