from django.contrib import admin

from .models import ForecastHour

# Register your models here. #


@admin.register(ForecastHour)
class ForecastHourAdmin(admin.ModelAdmin):
    # pyrefly: ignore[bad-override]
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
    # pyrefly: ignore[bad-override]
    list_filter = ("country_slug", "city_slug", "rating", "ok")
    # pyrefly: ignore[bad-override]
    search_fields = ("country_slug", "city_slug")
    # pyrefly: ignore[bad-override]
    ordering = ("-time",)
