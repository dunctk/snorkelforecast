from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import TypedDict
import logging

import httpx
from dateutil import tz
from django.core.cache import cache
from django.conf import settings
from .models import ForecastHour

CARBONERAS = {"lat": 36.997, "lon": -1.896}
THRESHOLDS = {
    "wave_height": 0.36,  # m
    "wind_speed": 5.4,  # m/s (~12 mph)
    "sea_surface_temperature": (20.6, 30.4),  # °C
}

THRESHOLDS.update(
    {
        "current_velocity": 0.36,  # m/s
        "slack_window_minutes": 72,
    }
)

logger = logging.getLogger(__name__)

# Cache settings
DEFAULT_FORECAST_CACHE_TTL = 600  # seconds
DEFAULT_FORECAST_STALE_TTL = 43200  # 12 hours for stale-if-error
DEFAULT_FORECAST_NEGATIVE_TTL = 120  # seconds to back off after API errors
FORECAST_CACHE_VERSION = 1


class Hour(TypedDict):
    time: datetime
    ok: bool
    score: float
    rating: str
    wave_height: float | None
    wind_speed: float | None
    sea_surface_temperature: float | None
    sea_level_height: float | None
    current_velocity: float | None
    wave_ok: bool
    wind_ok: bool
    sst_ok: bool
    slack_ok: bool
    is_high_tide: bool
    light_ok: bool
    sunrise: datetime
    sunset: datetime


def _calculate_score(
    wave: float | None, wind: float | None, sst: float | None, light_ok: bool
) -> float:
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
    else:  # sst > sst_max
        sst_score = max(0.0, 1 - ((sst - sst_max) / 5))

    # Final score is the product of individual scores
    return wave_score * wind_score * sst_score


def _rating_from_score(score: float, slack_ok: bool) -> str:
    """Map a numeric score and slack-tide state to a rating tier.

    Tiers:
    - excellent: score >= 0.8
    - good:      score >= 0.6
    - fair:      score >= 0.4
    - poor:      otherwise

    If not within the slack tide/current window, cap at 'fair'.
    """
    if score >= 0.8:
        rating = "excellent"
    elif score >= 0.6:
        rating = "good"
    elif score >= 0.4:
        rating = "fair"
    else:
        rating = "poor"

    if not slack_ok and rating in {"excellent", "good"}:
        rating = "fair"
    return rating


def _fallback_from_db(
    *, country_slug: str | None, city_slug: str | None, timezone_str: str, hours: int
) -> list[Hour]:
    """Return upcoming forecast from DB history if available.

    Uses stored values for score/rating; sunrise/sunset not included.
    Also flags high tides and slack windows based on stored tide/current.
    """
    if not country_slug or not city_slug:
        return []
    try:
        from django.utils import timezone as dj_tz

        qs = ForecastHour.objects.filter(
            country_slug=country_slug,
            city_slug=city_slug,
            time__gte=dj_tz.now(),
        ).order_by("time")
        rows = list(qs[: hours or 72])
        if not rows:
            return []
        # Build arrays to detect high tides and slack windows
        times = [r.time for r in rows]
        sea = [r.sea_level_height for r in rows]
        high_ix: list[int] = []
        for i in range(1, len(sea) - 1):
            prev, now, nxt = sea[i - 1], sea[i], sea[i + 1]
            if None not in (prev, now, nxt) and now is not None and now > prev and now > nxt:
                high_ix.append(i)

        window = timedelta(minutes=THRESHOLDS["slack_window_minutes"])
        slack_mask = [False] * len(times)
        for hi in high_ix:
            center = times[hi]
            for j, t in enumerate(times):
                if abs(t - center) <= window:
                    slack_mask[j] = True

        local = tz.gettz(timezone_str)
        result: list[Hour] = []
        for i, r in enumerate(rows):
            wave = r.wave_height
            wind = r.wind_speed
            sst = r.sea_surface_temperature
            current = r.current_velocity
            wave_ok = wave is not None and wave <= THRESHOLDS["wave_height"]
            wind_ok = wind is not None and wind <= THRESHOLDS["wind_speed"]
            sst_ok = (
                sst is not None
                and THRESHOLDS["sea_surface_temperature"][0]
                <= sst
                <= THRESHOLDS["sea_surface_temperature"][1]
            )
            slack_ok = (
                slack_mask[i] and current is not None and current <= THRESHOLDS["current_velocity"]
            )
            result.append(
                {
                    "time": r.time.astimezone(local),
                    "ok": r.ok,
                    "score": float(r.score),
                    "rating": r.rating,
                    "wave_height": wave,
                    "wind_speed": wind,
                    "sea_surface_temperature": sst,
                    "sea_level_height": r.sea_level_height,
                    "current_velocity": current,
                    "wave_ok": wave_ok,
                    "wind_ok": wind_ok,
                    "sst_ok": sst_ok,
                    "slack_ok": slack_ok,
                    "is_high_tide": i in high_ix,
                    "light_ok": True,
                    "sunrise": None,
                    "sunset": None,
                }
            )
        return result
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("DB fallback failed for %s/%s: %r", country_slug, city_slug, e)
        return []


def fetch_forecast(
    hours: int = 72,
    coordinates: dict | None = None,
    timezone_str: str | None = None,
    *,
    country_slug: str | None = None,
    city_slug: str | None = None,
) -> list[Hour]:
    """Return list of hours with snorkel suitability flag for any location."""
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

    # Cache key includes location, horizon, timezone, and a version for busting
    base_key = (
        f"forecast:v{FORECAST_CACHE_VERSION}:lat={coordinates['lat']:.5f}:lon={coordinates['lon']:.5f}:"
        f"h={hours}:tz={timezone_str}"
    )

    cache_key = base_key
    stale_key = base_key + ":stale"
    neg_key = base_key + ":neg"

    # Backoff if we recently saw an error; prefer stale if available
    if cache.get(neg_key):
        stale = cache.get(stale_key)
        if stale is not None:
            return stale
        # No stale available: try DB fallback
        db = _fallback_from_db(
            country_slug=country_slug,
            city_slug=city_slug,
            timezone_str=timezone_str,
            hours=hours,
        )
        if db:
            return db
        # Otherwise short-circuit to avoid hammering
        return []

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        with httpx.Client(timeout=10.0) as client:
            marine_response = client.get(marine_url)
            try:
                marine_response.raise_for_status()
            except httpx.HTTPError as e:
                # Log which endpoint failed and any response detail
                body = None
                try:
                    body = marine_response.text[:500]
                except Exception:
                    pass
                logger.warning(
                    "Marine API request failed: url=%s status=%s error=%r body_preview=%r",
                    marine_url,
                    getattr(marine_response, "status_code", "unknown"),
                    e,
                    body,
                )
                # Set negative cache/backoff and return stale if present
                try:
                    neg_ttl = int(
                        getattr(
                            settings, "FORECAST_CACHE_NEGATIVE_TTL", DEFAULT_FORECAST_NEGATIVE_TTL
                        )
                    )
                    cache.set(neg_key, True, timeout=neg_ttl)
                except Exception:
                    pass
                stale = cache.get(stale_key)
                if stale is not None:
                    return stale
                db = _fallback_from_db(
                    country_slug=country_slug,
                    city_slug=city_slug,
                    timezone_str=timezone_str,
                    hours=hours,
                )
                return db if db else []

            wx_response = client.get(wx_url)
            try:
                wx_response.raise_for_status()
            except httpx.HTTPError as e:
                body = None
                try:
                    body = wx_response.text[:500]
                except Exception:
                    pass
                logger.warning(
                    "Weather API request failed: url=%s status=%s error=%r body_preview=%r",
                    wx_url,
                    getattr(wx_response, "status_code", "unknown"),
                    e,
                    body,
                )
                try:
                    neg_ttl = int(
                        getattr(
                            settings, "FORECAST_CACHE_NEGATIVE_TTL", DEFAULT_FORECAST_NEGATIVE_TTL
                        )
                    )
                    cache.set(neg_key, True, timeout=neg_ttl)
                except Exception:
                    pass
                stale = cache.get(stale_key)
                if stale is not None:
                    return stale
                db = _fallback_from_db(
                    country_slug=country_slug,
                    city_slug=city_slug,
                    timezone_str=timezone_str,
                    hours=hours,
                )
                return db if db else []

            try:
                marine, wx = marine_response.json(), wx_response.json()
            except ValueError as e:
                logger.warning("Failed to decode API JSON: error=%r", e)
                try:
                    neg_ttl = int(
                        getattr(
                            settings, "FORECAST_CACHE_NEGATIVE_TTL", DEFAULT_FORECAST_NEGATIVE_TTL
                        )
                    )
                    cache.set(neg_key, True, timeout=neg_ttl)
                except Exception:
                    pass
                stale = cache.get(stale_key)
                if stale is not None:
                    return stale
                db = _fallback_from_db(
                    country_slug=country_slug,
                    city_slug=city_slug,
                    timezone_str=timezone_str,
                    hours=hours,
                )
                return db if db else []
    except httpx.TimeoutException as e:
        logger.warning("Forecast fetch timed out: error=%r", e)
        try:
            neg_ttl = int(
                getattr(settings, "FORECAST_CACHE_NEGATIVE_TTL", DEFAULT_FORECAST_NEGATIVE_TTL)
            )
            cache.set(neg_key, True, timeout=neg_ttl)
        except Exception:
            pass
        stale = cache.get(stale_key)
        if stale is not None:
            return stale
        db = _fallback_from_db(
            country_slug=country_slug,
            city_slug=city_slug,
            timezone_str=timezone_str,
            hours=hours,
        )
        return db if db else []
    except httpx.HTTPError as e:
        logger.warning("HTTP error during forecast fetch: error=%r", e)
        try:
            neg_ttl = int(
                getattr(settings, "FORECAST_CACHE_NEGATIVE_TTL", DEFAULT_FORECAST_NEGATIVE_TTL)
            )
            cache.set(neg_key, True, timeout=neg_ttl)
        except Exception:
            pass
        stale = cache.get(stale_key)
        if stale is not None:
            return stale
        db = _fallback_from_db(
            country_slug=country_slug,
            city_slug=city_slug,
            timezone_str=timezone_str,
            hours=hours,
        )
        return db if db else []

    local = tz.gettz(timezone_str)
    # Process daily sunrise/sunset data
    try:
        daily_times_utc = [datetime.fromisoformat(t).date() for t in wx["daily"]["time"]]
    except Exception as e:
        logger.warning("Malformed daily times from weather API: error=%r", e)
        return []
    sunrises = [
        datetime.fromisoformat(s).replace(tzinfo=timezone.utc).astimezone(local)
        for s in wx["daily"]["sunrise"]
    ]
    sunsets = [
        datetime.fromisoformat(s).replace(tzinfo=timezone.utc).astimezone(local)
        for s in wx["daily"]["sunset"]
    ]
    solar_map = {
        day: {"sunrise": sunrises[i], "sunset": sunsets[i]} for i, day in enumerate(daily_times_utc)
    }

    # Assume identical time arrays
    try:
        times_raw = marine["hourly"]["time"]
        if not times_raw:
            logger.warning("Marine API returned no hourly times: url=%s", marine_url)
            return []
        times_utc = [datetime.fromisoformat(t).replace(tzinfo=timezone.utc) for t in times_raw]
    except Exception as e:
        logger.warning("Malformed hourly times from marine API: error=%r", e)
        return []
    sea = marine["hourly"].get("sea_level_height_msl", [])
    curr = marine["hourly"].get("ocean_current_velocity", [])

    # Identify high tides (local maxima)
    high_ix: list[int] = []
    for i in range(1, len(sea) - 1):
        prev, now, nxt = sea[i - 1], sea[i], sea[i + 1]
        if None not in (prev, now, nxt) and now > prev and now > nxt:
            high_ix.append(i)

    window = timedelta(minutes=THRESHOLDS["slack_window_minutes"])
    slack_mask = [False] * len(times_utc)
    for hi in high_ix:
        center = times_utc[hi]
        for j, t in enumerate(times_utc):
            if abs(t - center) <= window:
                slack_mask[j] = True

    result: list[Hour] = []
    for i, t in enumerate(times_utc):
        wave = marine["hourly"]["wave_height"][i]
        sst = marine["hourly"]["sea_surface_temperature"][i]
        wind = wx["hourly"]["wind_speed_10m"][i]
        tide = sea[i] if i < len(sea) else None
        current = curr[i] if i < len(curr) else None

        wave_ok = wave is not None and wave <= THRESHOLDS["wave_height"]
        wind_ok = wind is not None and wind <= THRESHOLDS["wind_speed"]
        sst_ok = (
            sst is not None
            and THRESHOLDS["sea_surface_temperature"][0]
            <= sst
            <= THRESHOLDS["sea_surface_temperature"][1]
        )

        # Check light levels
        day = t.date()
        light_ok = False
        sunrise, sunset = None, None
        if day in solar_map:
            sunrise, sunset = solar_map[day]["sunrise"], solar_map[day]["sunset"]
            light_ok = sunrise <= t.astimezone(sunrise.tzinfo) <= sunset

        score = _calculate_score(wave, wind, sst, light_ok)

        slack_ok = (
            slack_mask[i] and current is not None and current <= THRESHOLDS["current_velocity"]
        )

        rating = _rating_from_score(score, slack_ok)
        ok = rating in {"excellent", "good"}

        result.append(
            {
                "time": t.astimezone(local),
                "ok": ok,
                "score": score,
                "rating": rating,
                "wave_height": wave,
                "wind_speed": wind,
                "sea_surface_temperature": sst,
                "sea_level_height": tide,
                "current_velocity": current,
                "wave_ok": wave_ok,
                "wind_ok": wind_ok,
                "sst_ok": sst_ok,
                "slack_ok": slack_ok,
                "is_high_tide": i in high_ix,
                "light_ok": light_ok,
                "sunrise": sunrise,
                "sunset": sunset,
            }
        )
    # Store in cache (fresh and stale) before returning
    try:
        ttl = int(getattr(settings, "FORECAST_CACHE_TTL", DEFAULT_FORECAST_CACHE_TTL))
        stale_ttl = int(getattr(settings, "FORECAST_CACHE_STALE_TTL", DEFAULT_FORECAST_STALE_TTL))
        cache.set(cache_key, result, timeout=ttl)
        cache.set(stale_key, result, timeout=stale_ttl)
    except Exception as e:
        logger.debug("Failed to set forecast cache: key=%s error=%r", cache_key, e)
    return result
