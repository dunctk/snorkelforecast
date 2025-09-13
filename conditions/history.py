from __future__ import annotations

from datetime import timedelta

from django.db.models import Avg
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .models import ForecastHour, SnorkelLocation


def save_forecast_history(
    location_or_country: str | SnorkelLocation, city_slug: str | None, hours: list[dict]
) -> None:
    """Persist forecast hours to DB for historical analysis.

    Uses bulk_create with ignore_conflicts to avoid duplicate rows for the
    same (location, time).

    Args:
        location_or_country: Either a SnorkelLocation instance or country_slug string
        city_slug: City slug string (ignored if location is provided)
        hours: List of forecast hour dictionaries
    """
    if not hours:
        return

    # Handle both old and new calling patterns
    if isinstance(location_or_country, SnorkelLocation):
        location = location_or_country
        country_slug = location.country_slug
        city_slug = location.city_slug
    else:
        location = None
        country_slug = location_or_country

    rows = []
    for h in hours:
        forecast_hour = ForecastHour(
            time=h.get("time"),
            ok=bool(h.get("ok")),
            score=float(h.get("score", 0.0)),
            rating=str(h.get("rating", "unknown")),
            wave_height=h.get("wave_height"),
            wind_speed=h.get("wind_speed"),
            sea_surface_temperature=h.get("sea_surface_temperature"),
            sea_level_height=h.get("sea_level_height"),
            current_velocity=h.get("current_velocity"),
            # Legacy fields for backward compatibility
            country_slug=country_slug,
            city_slug=city_slug,
        )
        if location:
            forecast_hour.location = location
        rows.append(forecast_hour)

    ForecastHour.objects.bulk_create(rows, ignore_conflicts=True)


def get_recent_averages(
    location_or_country: str | SnorkelLocation, city_slug: str | None = None, days: int = 30
) -> dict[str, float | None]:
    """Return average conditions for the recent period.

    Calculates averages for wave height, wind speed and sea surface temperature
    over the last ``days`` days.

    Args:
        location_or_country: Either a SnorkelLocation instance or country_slug string
        city_slug: City slug string (ignored if location is provided)
        days: Number of days to look back
    """

    cutoff = timezone.now() - timedelta(days=days)

    if isinstance(location_or_country, SnorkelLocation):
        qs = ForecastHour.objects.filter(location=location_or_country, time__gte=cutoff)
    else:
        qs = ForecastHour.objects.filter(
            country_slug=location_or_country, city_slug=city_slug, time__gte=cutoff
        )

    return qs.aggregate(
        avg_wave_height=Avg("wave_height"),
        avg_wind_speed=Avg("wind_speed"),
        avg_sea_temp=Avg("sea_surface_temperature"),
    )


def get_monthly_scores(
    location_or_country: str | SnorkelLocation, city_slug: str | None = None, months: int = 12
) -> list[dict[str, object]]:
    """Return monthly average snorkel scores for the past ``months`` months.

    Args:
        location_or_country: Either a SnorkelLocation instance or country_slug string
        city_slug: City slug string (ignored if location is provided)
        months: Number of months to look back
    """

    cutoff = timezone.now() - timedelta(days=months * 31)

    if isinstance(location_or_country, SnorkelLocation):
        qs = (
            ForecastHour.objects.filter(location=location_or_country, time__gte=cutoff)
            .annotate(month=TruncMonth("time"))
            .values("month")
            .annotate(avg_score=Avg("score"))
            .order_by("month")
        )
    else:
        qs = (
            ForecastHour.objects.filter(
                country_slug=location_or_country, city_slug=city_slug, time__gte=cutoff
            )
            .annotate(month=TruncMonth("time"))
            .values("month")
            .annotate(avg_score=Avg("score"))
            .order_by("month")
        )

    return list(qs)
