from django.contrib import admin

from .models import ForecastHour

# Register your models here.

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
