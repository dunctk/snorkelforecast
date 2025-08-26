from __future__ import annotations

from datetime import timedelta

from django.db.models import Avg
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .models import ForecastHour


def save_forecast_history(country_slug: str, city_slug: str, hours: list[dict]) -> None:
    """Persist forecast hours to DB for historical analysis.

    Uses bulk_create with ignore_conflicts to avoid duplicate rows for the
    same (country, city, time).
    """
    if not hours:
        return
    rows = []
    for h in hours:
        rows.append(
            ForecastHour(
                country_slug=country_slug,
                city_slug=city_slug,
                time=h.get("time"),
                ok=bool(h.get("ok")),
                score=float(h.get("score", 0.0)),
                rating=str(h.get("rating", "unknown")),
                wave_height=h.get("wave_height"),
                wind_speed=h.get("wind_speed"),
                sea_surface_temperature=h.get("sea_surface_temperature"),
                sea_level_height=h.get("sea_level_height"),
                current_velocity=h.get("current_velocity"),
            )
        )
    ForecastHour.objects.bulk_create(rows, ignore_conflicts=True)


def get_recent_averages(
    country_slug: str, city_slug: str, days: int = 30
) -> dict[str, float | None]:
    """Return average conditions for the recent period.

    Calculates averages for wave height, wind speed and sea surface temperature
    over the last ``days`` days.
    """

    cutoff = timezone.now() - timedelta(days=days)
    qs = ForecastHour.objects.filter(
        country_slug=country_slug, city_slug=city_slug, time__gte=cutoff
    )
    return qs.aggregate(
        avg_wave_height=Avg("wave_height"),
        avg_wind_speed=Avg("wind_speed"),
        avg_sea_temp=Avg("sea_surface_temperature"),
    )


def get_monthly_scores(
    country_slug: str, city_slug: str, months: int = 12
) -> list[dict[str, object]]:
    """Return monthly average snorkel scores for the past ``months`` months."""

    cutoff = timezone.now() - timedelta(days=months * 31)
    qs = (
        ForecastHour.objects.filter(
            country_slug=country_slug, city_slug=city_slug, time__gte=cutoff
        )
        .annotate(month=TruncMonth("time"))
        .values("month")
        .annotate(avg_score=Avg("score"))
        .order_by("month")
    )
    return list(qs)
