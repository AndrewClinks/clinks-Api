from django.urls import path

from .views import Detail

urlpatterns = [
    path('/<int:id>', Detail.as_view())
]
