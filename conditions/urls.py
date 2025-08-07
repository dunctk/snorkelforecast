from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('<str:country>/<str:city>/image.png', views.location_og_image, name='location_og_image'),
    path('<str:country>/<str:city>/', views.location_forecast, name='location_forecast'),
    path('carboneras/', views.home, name='legacy_home'),  # Legacy redirect
]