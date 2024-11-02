from django.urls import path

from .views import ListCreate, Detail

urlpatterns = [
    # The main ordering process happens with 2 calls to ListCreate
    path('', ListCreate.as_view()),
    # Detail is for updating to 'looking_for_driver' by vendor
    path('/<int:id>', Detail.as_view()),

]
