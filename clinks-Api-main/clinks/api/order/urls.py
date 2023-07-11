from django.urls import path

from .views import ListCreate, Detail

urlpatterns = [
    path('', ListCreate.as_view()),
    path('/<int:id>', Detail.as_view()),

]
