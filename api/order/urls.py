from django.urls import path

from .views import ListCreate, Detail

urlpatterns = [
    # POST for customers creating an order
    # But also GET, Patch, Delete
    path('', ListCreate.as_view()),
    # Detail is for updating to 'looking_for_driver' by vendor
    path('/<int:id>', Detail.as_view()),
]
