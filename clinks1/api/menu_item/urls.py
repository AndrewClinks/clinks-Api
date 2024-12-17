from django.urls import path

from .views import ListCreate, EditDelete, ListCreateV2

urlpatterns = [
    path('', ListCreate.as_view()),
    path('-v2', ListCreateV2.as_view()),

    path('/<int:id>', EditDelete.as_view()),
]
