from django.contrib import admin

from .models import AlertSubscription, ForecastHour

# Register your models here. #


@admin.register(ForecastHour)
class ForecastHourAdmin(admin.ModelAdmin):
    list_display = (
        "country_slug",
        "city_slug",
        "time",
        "rating",
        "ok",
        "wave_height",
        "wind_speed",
        "sea_surface_temperature",
    )
    list_filter = ("country_slug", "city_slug", "rating", "ok")
    search_fields = ("country_slug", "city_slug")
    ordering = ("-time",)


@admin.register(AlertSubscription)
class AlertSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "location", "min_rating", "is_active", "last_sent_at", "created_at")
    list_filter = ("is_active", "min_rating", "location__country_slug")
    search_fields = ("email", "location__name", "location__city_slug")
    ordering = ("-created_at",)
