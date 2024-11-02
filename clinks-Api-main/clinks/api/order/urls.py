from django.urls import path

from .views import ListCreate, Detail

urlpatterns = [
    # The main ordering process happens with 2 calls to ListCreate
    # Detail is for getting updating a specific order details after payment
    path('', ListCreate.as_view()),
    path('/<int:id>', Detail.as_view()),

]
