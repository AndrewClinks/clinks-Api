from django.urls import path

from .views import Create, Detail

urlpatterns = [
    path('', Create.as_view()),
    path('/<int:id>', Detail.as_view()),
]