from django.urls import path, re_path
from . import views

urlpatterns = [
    # IndexNow key verification file (/<hexkey>.txt). Hex-only + .txt suffix so it
    # never collides with country/city slugs.
    re_path(r"^(?P<key>[a-f0-9]{16,64})\.txt$", views.indexnow_key_file, name="indexnow_key_file"),
    path("api/search-locations/", views.location_search_api, name="location_search_api"),
    path("buscar/", views.location_search, name="location_search_es"),
    path("search/", views.location_search, name="location_search"),
    path("mejor-snorkel/", views.best_snorkeling, name="best_snorkeling_es"),
    path("best-snorkeling/", views.best_snorkeling, name="best_snorkeling"),
    path("guias/", views.guides_index, name="guides_index_es"),
    path("guias/<slug:slug>/", views.guide_detail, name="guide_detail_es"),
    path("guides/", views.guides_index, name="guides_index"),
    path("guides/<slug:slug>/", views.guide_detail, name="guide_detail"),
    path("health/", views.health_check, name="health_check"),
    path(
        "alerts/unsubscribe/<str:token>/",
        views.alert_unsubscribe,
        name="alert_unsubscribe",
    ),
    path("", views.homepage, name="homepage"),
    # Site-wide OG image
    path("og.png", views.site_og_image, name="site_og_image"),
    # Countries index must be above the generic country slug route
    path("destinos/", views.countries_index, name="countries_index_es"),
    path("countries/", views.countries_index, name="countries_index"),
    path("espana/", views.country_directory, {"country": "spain"}, name="country_directory_spain_es"),
    path(
        "espana/<str:city>/historial/",
        views.location_history,
        {"country": "spain"},
        name="location_history_spain_es",
    ),
    path(
        "espana/<str:city>/temperatura-del-mar/",
        views.location_sea_temperature,
        {"country": "spain"},
        name="location_sea_temperature_spain_es",
    ),
    path(
        "espana/<str:city>/alertas/",
        views.location_alert_subscribe,
        {"country": "spain"},
        name="location_alert_subscribe_spain_es",
    ),
    path(
        "espana/<str:city>/",
        views.location_forecast,
        {"country": "spain"},
        name="location_forecast_spain_es",
    ),
    path("estados-unidos/", views.country_directory, {"country": "usa"}, name="country_directory_usa_es"),
    path(
        "estados-unidos/<str:city>/historial/",
        views.location_history,
        {"country": "usa"},
        name="location_history_usa_es",
    ),
    path(
        "estados-unidos/<str:city>/temperatura-del-mar/",
        views.location_sea_temperature,
        {"country": "usa"},
        name="location_sea_temperature_usa_es",
    ),
    path(
        "estados-unidos/<str:city>/alertas/",
        views.location_alert_subscribe,
        {"country": "usa"},
        name="location_alert_subscribe_usa_es",
    ),
    path(
        "estados-unidos/<str:city>/",
        views.location_forecast,
        {"country": "usa"},
        name="location_forecast_usa_es",
    ),
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
        "<str:country>/<str:city>/historial/",
        views.location_history,
        name="location_history_es",
    ),
    path(
        "<str:country>/<str:city>/sea-temperature/",
        views.location_sea_temperature,
        name="location_sea_temperature",
    ),
    path(
        "<str:country>/<str:city>/temperatura-del-mar/",
        views.location_sea_temperature,
        name="location_sea_temperature_es",
    ),
    path(
        "<str:country>/<str:city>/embed/sea-temperature/",
        views.location_sea_temperature_embed,
        name="location_sea_temperature_embed",
    ),
    path(
        "<str:country>/<str:city>/alerts/",
        views.location_alert_subscribe,
        name="location_alert_subscribe",
    ),
    path(
        "<str:country>/<str:city>/alertas/",
        views.location_alert_subscribe,
        name="location_alert_subscribe_es",
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
