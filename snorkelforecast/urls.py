from django.urls import path
from conditions.views import home

urlpatterns = [
    path("", home, name="home"),
]
