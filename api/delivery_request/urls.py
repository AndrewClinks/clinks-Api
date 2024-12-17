from django.urls import path

from .views import List, Detail

urlpatterns = [
    path('', List.as_view()),
    path('/<int:id>', Detail.as_view())
]
