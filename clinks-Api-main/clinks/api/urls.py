from django.conf.urls import include
from django.urls import path
from django.conf import settings

urlpatterns = [
    path("user", include("api.user.urls")),

    path("admins", include("api.admin.urls")),

    path("customers", include("api.customer.urls")),

    path("images", include("api.image.urls")),

    path("drivers", include("api.driver.urls")),

    path("companies", include("api.company.urls")),

    path("company-members", include("api.company_member.urls")),

    path("delivery-distances", include("api.delivery_distance.urls")),

    path("venues", include("api.venue.urls")),

    path("staff", include("api.staff.urls")),

    path("categories", include("api.category.urls")),

    path("items", include("api.item.urls")),

    path("menus", include("api.menu.urls")),

    path("menu-categories", include("api.menu_category.urls")),

    path("menu-items", include("api.menu_item.urls")),

    path("cards", include("api.card.urls")),

    path("stripe-connect", include("api.stripe_connect.urls")),

    path("webhooks", include("api.webhooks.urls")),

    path("settings", include("api.setting.urls")),

    path("status", include("api.status.urls")),

    path("orders", include("api.order.urls")),

    path("all-time-stats", include("api.all_time_stat.urls")),

    path("daily-stats", include("api.daily_stat.urls")),

    path("delivery-requests", include("api.delivery_request.urls")),

    path("payments", include("api.payment.urls")),

    path("driver-payments", include("api.driver_payment.urls")),

    path("delivery-fees", include("api.delivery_fee.urls"))
]

if settings.DEBUG:
    from .utils.Notification import SendNotification
    urlpatterns = [
        path('send-notification', SendNotification.as_view()),
    ] + urlpatterns