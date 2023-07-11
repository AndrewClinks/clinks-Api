from django.urls import path
from .views import (Connect, )

urlpatterns = [
    path("", Connect.as_view()),

]
