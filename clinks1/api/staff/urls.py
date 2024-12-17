from django.urls import path

from .views import ListCreate, Delete

urlpatterns = [
    path('', ListCreate.as_view()),
    path('/<int:id>', Delete.as_view())
]
