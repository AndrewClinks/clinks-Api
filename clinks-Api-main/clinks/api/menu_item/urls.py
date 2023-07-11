from django.urls import path

from .views import ListCreate, EditDelete

urlpatterns = [
    path('', ListCreate.as_view()),
    path('/<int:id>', EditDelete.as_view()),
]
