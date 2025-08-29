from django.urls import path
from . import views

urlpatterns = [
    path("api/search-locations/", views.location_search_api, name="location_search_api"),
    path("", views.homepage, name="homepage"),
    # Site-wide OG image
    path("og.png", views.site_og_image, name="site_og_image"),
    # Countries index must be above the generic country slug route
    path("countries/", views.countries_index, name="countries_index"),
    path(
        "<str:country>/<str:city>/history.json",
        views.location_history_api,
        name="location_history_api",
    ),
    path(
        "<str:country>/<str:city>/history/",
        views.location_history,
        name="location_history",
    ),
    path(
        "<str:country>/<str:city>/tide.png", views.location_tide_chart, name="location_tide_chart"
    ),
    path("<str:country>/<str:city>/image.png", views.location_og_image, name="location_og_image"),
    path("<str:country>/<str:city>/", views.location_forecast, name="location_forecast"),
    path("carboneras/", views.home, name="legacy_home"),  # Legacy redirect
    # Country directory page (must come after specific legacy routes)
    path("<str:country>/", views.country_directory, name="country_directory"),
]
