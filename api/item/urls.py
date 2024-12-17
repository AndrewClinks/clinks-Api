from django.urls import path

from .views import ListCreate, EditDelete, Import

urlpatterns = [
    path('', ListCreate.as_view()),
    path('/<int:id>', EditDelete.as_view()),
    path('/import', Import.as_view())
]
