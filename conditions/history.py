from __future__ import annotations

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
