from django.urls import path

from .views import Detail, MenuCategoryDetails

urlpatterns = [
    path('/<int:id>', Detail.as_view()),
    path('/<int:id>/categories', MenuCategoryDetails.as_view()),

]
