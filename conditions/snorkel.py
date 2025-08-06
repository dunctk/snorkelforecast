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
    "current_velocity": 0.3,   # m/s
    "slack_window_minutes": 60,
}

class Hour(TypedDict):
    time: datetime
    ok: bool
    score: float
    wave_height: float | None
    wind_speed: float | None
    sea_surface_temperature: float | None
    sea_level_height: float | None
    current_velocity: float | None
    wave_ok: bool
    wind_ok: bool
    sst_ok: bool
    current_ok: bool
    slack_ok: bool
    light_ok: bool
    sunrise: datetime
    sunset: datetime


def _calculate_score(wave: float | None, wind: float | None, sst: float | None, light_ok: bool) -> float:
    """Calculate a snorkel score from 0 to 1 based on conditions."""
    if not light_ok or wave is None or wind is None or sst is None:
        return 0.0

    # Normalise each metric to a 0-1 score
    wave_score = max(0.0, 1 - (wave / (THRESHOLDS["wave_height"] * 2)))
    wind_score = max(0.0, 1 - (wind / (THRESHOLDS["wind_speed"] * 2)))

    # SST score is 1 inside the ideal range, and drops off outside it
    sst_min, sst_max = THRESHOLDS["sea_surface_temperature"]
    if sst_min <= sst <= sst_max:
        sst_score = 1.0
    elif sst < sst_min:
        sst_score = max(0.0, 1 - ((sst_min - sst) / 5))
    else: # sst > sst_max
        sst_score = max(0.0, 1 - ((sst - sst_max) / 5))

    # Final score is the product of individual scores
    return wave_score * wind_score * sst_score


def fetch_forecast(hours: int = 72, coordinates: dict = None, timezone_str: str = None) -> tuple[list[Hour], list[datetime]]:
    """Return list of hourly conditions and high tide times for any location."""
    # Use provided coordinates or default to Carboneras
    if coordinates is None:
        coordinates = CARBONERAS
    if timezone_str is None:
        timezone_str = "Europe/Madrid"
        
    marine_url = (
        "https://marine-api.open-meteo.com/v1/marine"
        f"?latitude={coordinates['lat']}&longitude={coordinates['lon']}"
        "&hourly=wave_height,sea_surface_temperature,sea_level_height_msl,ocean_current_velocity"
        "&timezone=UTC"
        f"&past_hours=0&forecast_hours={hours}"
    )
    wx_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={coordinates['lat']}&longitude={coordinates['lon']}"
        "&hourly=wind_speed_10m&daily=sunrise,sunset"
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
    except (httpx.HTTPError, httpx.TimeoutException):
        # Return empty forecast on API failure
        return []

    local = tz.gettz(timezone_str)
    # Process daily sunrise/sunset data
    daily_times_utc = [datetime.fromisoformat(t).date() for t in wx["daily"]["time"]]
    sunrises = [datetime.fromisoformat(s).replace(tzinfo=timezone.utc).astimezone(local) for s in wx["daily"]["sunrise"]]
    sunsets = [datetime.fromisoformat(s).replace(tzinfo=timezone.utc).astimezone(local) for s in wx["daily"]["sunset"]]
    solar_map = {day: {"sunrise": sunrises[i], "sunset": sunsets[i]} for i, day in enumerate(daily_times_utc)}

    # Assume identical time arrays
    times_utc = [datetime.fromisoformat(t).replace(tzinfo=timezone.utc) for t in marine["hourly"]["time"]]
    sea_levels = marine["hourly"].get("sea_level_height_msl", [])
    currents = marine["hourly"].get("ocean_current_velocity", [])

    # Detect high tides
    high_tide_indices: list[int] = []
    for i in range(1, len(sea_levels) - 1):
        prev_h, curr_h, next_h = sea_levels[i - 1], sea_levels[i], sea_levels[i + 1]
        if None not in (prev_h, curr_h, next_h) and curr_h > prev_h and curr_h > next_h:
            high_tide_indices.append(i)
    high_tide_times = [times_utc[i] for i in high_tide_indices]

    # Pre-compute slack flags for each hour
    slack_window = THRESHOLDS["slack_window_minutes"] * 60
    slack_flags: list[bool] = []
    for t in times_utc:
        slack_flags.append(any(abs((t - ht).total_seconds()) <= slack_window for ht in high_tide_times))

    result: list[Hour] = []
    for i, t in enumerate(times_utc):
        wave = marine["hourly"]["wave_height"][i]
        sst = marine["hourly"]["sea_surface_temperature"][i]
        wind = wx["hourly"]["wind_speed_10m"][i]
        sea_level = sea_levels[i] if i < len(sea_levels) else None
        current = currents[i] if i < len(currents) else None

        wave_ok = wave is not None and wave <= THRESHOLDS["wave_height"]
        wind_ok = wind is not None and wind <= THRESHOLDS["wind_speed"]
        sst_ok = sst is not None and THRESHOLDS["sea_surface_temperature"][0] <= sst <= THRESHOLDS["sea_surface_temperature"][1]
        current_ok = current is not None and current <= THRESHOLDS["current_velocity"]
        slack_ok = slack_flags[i]

        # Check light levels
        day = t.date()
        light_ok = False
        sunrise, sunset = None, None
        if day in solar_map:
            sunrise, sunset = solar_map[day]["sunrise"], solar_map[day]["sunset"]
            light_ok = sunrise <= t.astimezone(sunrise.tzinfo) <= sunset

        score = _calculate_score(wave, wind, sst, light_ok)
        ok = score > 0.5 and current_ok and slack_ok

        result.append({
            "time": t.astimezone(local),
            "ok": ok,
            "score": score,
            "wave_height": wave,
            "wind_speed": wind,
            "sea_surface_temperature": sst,
            "sea_level_height": sea_level,
            "current_velocity": current,
            "wave_ok": wave_ok,
            "wind_ok": wind_ok,
            "sst_ok": sst_ok,
            "current_ok": current_ok,
            "slack_ok": slack_ok,
            "light_ok": light_ok,
            "sunrise": sunrise,
            "sunset": sunset,
        })

    high_tides_local = [t.astimezone(local) for t in high_tide_times]
    return result, high_tides_local