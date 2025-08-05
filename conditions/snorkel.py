from __future__ import annotations

from datetime import datetime, timezone
from typing import TypedDict

import httpx
from dateutil import tz

CARBONERAS = {"lat": 36.997, "lon": -1.896}
THRESHOLDS = {
    "wave_height": 0.3,        # m
    "wind_speed": 4.5,         # m/s (~10 mph)
    "sea_surface_temperature": (22, 29),  # °C
}

class Hour(TypedDict):
    time: datetime
    ok: bool


def fetch_forecast(hours: int = 72) -> list[Hour]:
    """Return list of hours with snorkel suitability flag (Carboneras only)."""
    marine_url = (
        "https://marine-api.open-meteo.com/v1/marine"
        f"?latitude={CARBONERAS['lat']}&longitude={CARBONERAS['lon']}"
        "&hourly=wave_height,sea_surface_temperature"
        "&timezone=UTC"
        f"&past_hours=0&forecast_hours={hours}"
    )
    wx_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={CARBONERAS['lat']}&longitude={CARBONERAS['lon']}"
        "&hourly=wind_speed_10m"
        "&timezone=UTC"
        f"&past_hours=0&forecast_hours={hours}"
    )
    
    try:
        with httpx.Client(timeout=10.0) as client:
            marine_response = client.get(marine_url)
            marine_response.raise_for_status()
            wx_response = client.get(wx_url)
            wx_response.raise_for_status()
            marine, wx = marine_response.json(), wx_response.json()
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        # Return empty forecast on API failure
        return []

    # Assume identical time arrays
    times_utc = [datetime.fromisoformat(t).replace(tzinfo=timezone.utc) for t in marine["hourly"]["time"]]
    local = tz.gettz("Europe/Madrid")

    result: list[Hour] = []
    for i, t in enumerate(times_utc):
        wave = marine["hourly"]["wave_height"][i]
        sst = marine["hourly"]["sea_surface_temperature"][i]
        wind = wx["hourly"]["wind_speed_10m"][i]

        ok = (
            wave is not None and wave <= THRESHOLDS["wave_height"] and
            wind is not None and wind <= THRESHOLDS["wind_speed"] and
            sst is not None and THRESHOLDS["sea_surface_temperature"][0] <= sst <= THRESHOLDS["sea_surface_temperature"][1]
        )
        result.append({"time": t.astimezone(local), "ok": ok})
    return result