from django.urls import path
from .views import ListCreate, Edit

urlpatterns = [
    path('', ListCreate.as_view()),
    path('/<int:id>', Edit.as_view()),

]