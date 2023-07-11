from django.urls import path, include
from rest_framework.routers import DefaultRouter

from push_notifications.api.rest_framework import (
    APNSDeviceAuthorizedViewSet,
    GCMDeviceAuthorizedViewSet
)

from .views import (
    Login,
    Logout,
    Refresh,
    Info,
    RequestPasswordReset,
    ResetPassword,
    RequestVerifyEmail,
    VerifyEmail
)

push_notifications_router = DefaultRouter(trailing_slash=False)
push_notifications_router.register(r'apns', APNSDeviceAuthorizedViewSet)
push_notifications_router.register(r'gcm', GCMDeviceAuthorizedViewSet)

urlpatterns = [
    path('/login', Login.as_view()),
    path('/logout', Logout.as_view()),
    path('/refresh-token', Refresh.as_view()),
    path('/info', Info.as_view()),
    path('/request-reset-password', RequestPasswordReset.as_view()),
    path('/reset-password', ResetPassword.as_view()),
    path("/request-verify-email", RequestVerifyEmail.as_view()),
    path("/verify-email", VerifyEmail.as_view()),
    path('/device/', include(push_notifications_router.urls)),
]