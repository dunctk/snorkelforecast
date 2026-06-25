from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from typing import TypedDict
import logging

import httpx
from dateutil import tz
from django.core.cache import cache
from django.utils import timezone as dj_timezone
from django.conf import settings
from .models import ForecastHour, LocationForecastSnapshot, SnorkelLocation

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

# Cache settings from Django settings
DEFAULT_FORECAST_CACHE_TTL = getattr(settings, "FORECAST_CACHE_TTL", 21600)  # 6 hours
DEFAULT_FORECAST_STALE_TTL = getattr(settings, "FORECAST_CACHE_STALE_TTL", 86400)  # 24 hours
DEFAULT_FORECAST_NEGATIVE_TTL = getattr(settings, "FORECAST_CACHE_NEGATIVE_TTL", 1800)  # 30 minutes
DEFAULT_FORECAST_REQUEST_TIMEOUT = getattr(settings, "FORECAST_REQUEST_TIMEOUT", 5.0)
FORECAST_CACHE_VERSION = 1
SNAPSHOT_VERSION = 1


def _to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _from_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


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
    tide_score: float
    cloud_cover: float | None


def _tide_score(
    sea_level_height: float | None,
    current_velocity: float | None,
    is_slack: bool,
    is_rising: bool | None,
    tidal_range: float | None,
) -> float:
    """Return a tide/current score in [0.0, 1.0].

    Maps the user-facing scoring model (‑20 to +20) into a 0–1 scale:

      raw 20 → 1.0   high slack, low current
      raw 12 → 0.8   near high tide (slack but some current)
      raw  8 → 0.7   approaching high tide (rising)
      raw  5 → 0.625 after high tide (falling)
      raw  0 → 0.5   neutral / no data
      raw -10 → 0.25 strong current
      raw -20 → 0.0  very low tide / exposed rocks
      raw -30 → 0.0  combined penalties (clamped)
    """
    raw = 0  # → 0.5 after normalisation

    if sea_level_height is not None:
        if is_slack and current_velocity is not None and current_velocity <= THRESHOLDS["current_velocity"]:
            raw = 20
        elif is_slack:
            raw = 12
        elif is_rising is True:
            raw = 8
        elif is_rising is False:
            raw = 5

        # Strong current penalty (overrides weaker positive scores)
        if current_velocity is not None and current_velocity > 0.5:
            raw = -10

        # Very low tide — severe penalty
        if sea_level_height < -0.5:
            raw = -20

        # Spring-tide / large tidal-range penalty
        if tidal_range is not None and tidal_range > 2.0:
            raw -= 10

    return max(0.0, min(1.0, (raw + 20) / 40))


def _calculate_score(
    wave: float | None,
    wind: float | None,
    sst: float | None,
    tide_score: float,
    light_ok: bool,
    cloud_cover: float | None = None,
) -> float:
    """Calculate a snorkel score from 0 to 1 based on conditions.

    Factors are combined as a weighted sum (tide/current included as a
    modifier) rather than a pure product.  Daylight remains a hard gate
    for safety.
    """
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

    cloud_score = _cloud_score(cloud_cover)
    # Weighted sum with tide as modifier, daylight as hard gate (bonus 0.10)
    base_score = (
        wave_score * 0.35
        + wind_score * 0.25
        + sst_score * 0.15
        + tide_score * 0.15
        + 0.10  # daylight bonus (already gated on light_ok)
    )
    # Clear skies should help visibility and heavily overcast windows should
    # reduce snorkelability even when other metrics are acceptable.
    score = base_score - ((1.0 - cloud_score) * 0.30)
    return max(0.0, min(1.0, score))


def _rating_from_score(score: float) -> str:
    """Map a numeric score to a rating tier.

    Tiers:
    - excellent: score >= 0.8
    - good:      score >= 0.6
    - fair:      score >= 0.4
    - poor:      otherwise

    Tide/current is baked into the score, so no separate cap is needed.
    """
    if score >= 0.8:
        return "excellent"
    elif score >= 0.6:
        return "good"
    elif score >= 0.4:
        return "fair"
    else:
        return "poor"



def _cloud_score(cloud_cover: float | None) -> float:
    """Map cloud cover percentage to a visibility score from 1.0 to 0.0."""
    if cloud_cover is None:
        return 1.0
    try:
        cloud_pct = float(cloud_cover)
    except (TypeError, ValueError):
        return 1.0

    if cloud_pct <= 0:
        return 1.0
    if cloud_pct >= 100:
        return 0.0
    return max(0.0, 1 - (cloud_pct / 100.0))


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

        # Tidal range for spring-tide penalty
        valid_sea = [s for s in sea if s is not None]
        tidal_range = (max(valid_sea) - min(valid_sea)) if len(valid_sea) > 1 else None

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
            cloud_cover = None

            # Tide direction: rising vs falling
            prev_sea = sea[i - 1] if i > 0 else None
            is_rising = None
            if prev_sea is not None and sea[i] is not None:
                is_rising = sea[i] > prev_sea

            tide_score = _tide_score(sea[i], current, slack_mask[i], is_rising, tidal_range)
            score = _calculate_score(wave, wind, sst, tide_score, True, cloud_cover)

            result.append(
                {
                    "time": r.time.astimezone(local),
                    "ok": r.ok,
                    "score": score,
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
                    "tide_score": tide_score,
                    "cloud_cover": cloud_cover,
                }
            )
        return result
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("DB fallback failed for %s/%s: %r", country_slug, city_slug, e)
        return []


def _snapshot_key(
    *,
    coordinates: dict | None,
    hours: int,
    country_slug: str | None,
    city_slug: str | None,
    location: SnorkelLocation | None,
) -> str:
    """Build a stable cache key for snapshot rows."""
    if location is not None and location.pk:
        return (
            f"forecast-snapshot:v{SNAPSHOT_VERSION}:loc={location.pk}:h={hours}"
        )

    if country_slug and city_slug:
        return (
            f"forecast-snapshot:v{SNAPSHOT_VERSION}:{country_slug}:{city_slug}:h={hours}"
        )

    # Last resort: use rounded coordinates to avoid churn on high-precision values.
    if coordinates is None:
        return f"forecast-snapshot:v{SNAPSHOT_VERSION}:default:h={hours}"
    return (
        f"forecast-snapshot:v{SNAPSHOT_VERSION}:lat={coordinates['lat']:.5f}:"
        f"lon={coordinates['lon']:.5f}:h={hours}"
    )


def _serialize_snapshot_hours(hours: list[Hour]) -> list[dict]:
    payload: list[dict] = []
    for h in hours:
        t = h.get("time")
        if not isinstance(t, datetime):
            continue
        payload.append(
            {
                "time": _to_iso(t),
                "ok": bool(h.get("ok")),
                "score": h.get("score"),
                "rating": h.get("rating"),
                "wave_height": h.get("wave_height"),
                "wind_speed": h.get("wind_speed"),
                "sea_surface_temperature": h.get("sea_surface_temperature"),
                "sea_level_height": h.get("sea_level_height"),
                "current_velocity": h.get("current_velocity"),
                "wave_ok": h.get("wave_ok"),
                "wind_ok": h.get("wind_ok"),
                "sst_ok": h.get("sst_ok"),
                "slack_ok": h.get("slack_ok"),
                "is_high_tide": h.get("is_high_tide"),
                "light_ok": h.get("light_ok"),
                "sunrise": _to_iso(h.get("sunrise")),
                "sunset": _to_iso(h.get("sunset")),
                "tide_score": h.get("tide_score"),
                "cloud_cover": h.get("cloud_cover"),
            }
        )
    return payload


def _deserialize_snapshot_rows(snapshot_hours: list[object]) -> list[Hour]:
    hours: list[Hour] = []
    for row in snapshot_hours:
        if not isinstance(row, dict):
            continue

        time = _from_iso(row.get("time"))
        if not isinstance(time, datetime):
            continue

        hours.append(
            {
                "time": time,
                "ok": bool(row.get("ok")),
                "score": row.get("score") if isinstance(row.get("score"), (float, int)) else 0.0,
                "rating": row.get("rating") or "poor",
                "wave_height": row.get("wave_height"),
                "wind_speed": row.get("wind_speed"),
                "sea_surface_temperature": row.get("sea_surface_temperature"),
                "sea_level_height": row.get("sea_level_height"),
                "current_velocity": row.get("current_velocity"),
                "wave_ok": row.get("wave_ok") if row.get("wave_ok") is not None else False,
                "wind_ok": row.get("wind_ok") if row.get("wind_ok") is not None else False,
                "sst_ok": row.get("sst_ok") if row.get("sst_ok") is not None else False,
                "slack_ok": row.get("slack_ok") if row.get("slack_ok") is not None else False,
                "is_high_tide": row.get("is_high_tide") if row.get("is_high_tide") is not None else False,
                "light_ok": row.get("light_ok") if row.get("light_ok") is not None else False,
                "sunrise": _from_iso(row.get("sunrise")),
                "sunset": _from_iso(row.get("sunset")),
                "tide_score": row.get("tide_score")
                if isinstance(row.get("tide_score"), (float, int))
                else 0.0,
                "cloud_cover": row.get("cloud_cover"),
            }
        )
    return hours


def _load_forecast_snapshot(snapshot_key: str) -> tuple[list[Hour], datetime | None, datetime | None]:
    try:
        snapshot = LocationForecastSnapshot.objects.get(snapshot_key=snapshot_key)
    except LocationForecastSnapshot.DoesNotExist:
        return [], None, None

    payload = _deserialize_snapshot_rows(snapshot.snapshot_hours)
    if not payload:
        return [], snapshot.generated_at, snapshot.valid_until
    return payload, snapshot.generated_at, snapshot.valid_until


def _save_forecast_snapshot(
    snapshot_key: str,
    *,
    coordinates: dict | None,
    timezone_str: str,
    country_slug: str | None,
    city_slug: str | None,
    location: SnorkelLocation | None,
    hours: int,
    payload: list[Hour],
) -> None:
    try:
        stale_ttl = int(getattr(settings, "FORECAST_CACHE_STALE_TTL", DEFAULT_FORECAST_STALE_TTL))
        generated_at = dj_timezone.now()
        valid_until = generated_at + timedelta(seconds=stale_ttl)

        LocationForecastSnapshot.objects.update_or_create(
            snapshot_key=snapshot_key,
            defaults={
                "location": location,
                "country_slug": country_slug or "",
                "city_slug": city_slug or "",
                "timezone": timezone_str,
                "horizon_hours": hours,
                "snapshot_hours": _serialize_snapshot_hours(payload),
                "generated_at": generated_at,
                "valid_until": valid_until,
            },
        )
    except Exception as e:  # pragma: no cover - defensive for DB issues
        logger.debug("Failed to save forecast snapshot: key=%s error=%r", snapshot_key, e)


def _build_cache_keys(
    *, coordinates: dict, hours: int, timezone_str: str
) -> tuple[str, str, str]:
    base_key = (
        f"forecast:v{FORECAST_CACHE_VERSION}:lat={coordinates['lat']:.5f}:"
        f"lon={coordinates['lon']:.5f}:h={hours}:tz={timezone_str}"
    )
    return base_key, base_key + ":stale", base_key + ":neg"


def _fallback_payload(hours: int, timezone_str: str, country_slug: str | None, city_slug: str | None) -> dict:
    db = _fallback_from_db(
        country_slug=country_slug,
        city_slug=city_slug,
        timezone_str=timezone_str,
        hours=hours,
    )
    if db:
        return {
            "hours": db,
            "source": "db_fallback",
            "generated_at": dj_timezone.now(),
            "next_refresh_at": None,
            "is_stale": True,
        }
    return {
        "hours": [],
        "source": "unavailable",
        "generated_at": None,
        "next_refresh_at": None,
        "is_stale": True,
    }


def _api_fetch_hours(
    *,
    coordinates: dict,
    hours: int,
    timezone_str: str,
    country_slug: str | None,
    city_slug: str | None,
    cache_key: str,
    stale_key: str,
    neg_key: str,
) -> dict:
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
        "&hourly=wind_speed_10m,cloud_cover&daily=sunrise,sunset"
        "&timezone=UTC"
        f"&past_hours=0&forecast_hours={hours}"
    )

    try:
        request_timeout = float(
            getattr(settings, "FORECAST_REQUEST_TIMEOUT", DEFAULT_FORECAST_REQUEST_TIMEOUT)
        )
        timeout = httpx.Timeout(
            request_timeout,
            connect=min(request_timeout, 2.0),
            pool=min(request_timeout, 2.0),
        )
        with httpx.Client(timeout=timeout) as client:
            with ThreadPoolExecutor(max_workers=2) as executor:
                marine_future = executor.submit(client.get, marine_url)
                wx_future = executor.submit(client.get, wx_url)

                marine_response = marine_future.result()
                wx_response = wx_future.result()

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
                raise

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
                raise

            try:
                marine, wx = marine_response.json(), wx_response.json()
            except ValueError as e:
                logger.warning("Failed to decode API JSON: error=%r", e)
                raise
    except (httpx.TimeoutException, httpx.HTTPError) as e:
        logger.warning("Forecast fetch failed: error=%r", e)
        raise

    local = tz.gettz(timezone_str)
    # Process daily sunrise/sunset data
    try:
        daily_times_utc = [datetime.fromisoformat(t).date() for t in wx["daily"]["time"]]
    except Exception as e:
        logger.warning("Malformed daily times from weather API: error=%r", e)
        raise ValueError("Malformed daily times")

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
            return {
                "hours": [],
                "source": "api_empty",
                "generated_at": dj_timezone.now(),
                "next_refresh_at": None,
                "is_stale": False,
            }
        times_utc = [datetime.fromisoformat(t).replace(tzinfo=timezone.utc) for t in times_raw]
    except Exception as e:
        logger.warning("Malformed hourly times from marine API: error=%r", e)
        raise

    sea = marine["hourly"].get("sea_level_height_msl", [])
    curr = marine["hourly"].get("ocean_current_velocity", [])
    cloud_cover = wx["hourly"].get("cloud_cover", [])

    # Identify high tides (local maxima)
    high_ix: list[int] = []
    for i in range(1, len(sea) - 1):
        prev, now, nxt = sea[i - 1], sea[i], sea[i + 1]
        if None not in (prev, now, nxt) and now is not None and now > prev and now > nxt:
            high_ix.append(i)

    window = timedelta(minutes=THRESHOLDS["slack_window_minutes"])
    slack_mask = [False] * len(times_utc)
    for hi in high_ix:
        center = times_utc[hi]
        for j, t in enumerate(times_utc):
            if abs(t - center) <= window:
                slack_mask[j] = True

    # Tidal range for spring-tide penalty
    valid_sea = [s for s in sea if s is not None]
    tidal_range = (max(valid_sea) - min(valid_sea)) if len(valid_sea) > 1 else None

    result: list[Hour] = []
    for i, t in enumerate(times_utc):
        wave = marine["hourly"]["wave_height"][i]
        sst = marine["hourly"]["sea_surface_temperature"][i]
        wind = wx["hourly"]["wind_speed_10m"][i]
        tide = sea[i] if i < len(sea) else None
        current = curr[i] if i < len(curr) else None
        this_cloud_cover = cloud_cover[i] if i < len(cloud_cover) else None

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

        # Tide direction: rising vs falling
        prev_sea = sea[i - 1] if i > 0 else None
        is_rising = None
        if prev_sea is not None and tide is not None:
            is_rising = tide > prev_sea

        tide_score_val = _tide_score(tide, current, slack_mask[i], is_rising, tidal_range)
        score = _calculate_score(
            wave,
            wind,
            sst,
            tide_score_val,
            light_ok,
            this_cloud_cover,
        )

        slack_ok = slack_mask[i] and current is not None and current <= THRESHOLDS["current_velocity"]

        rating = _rating_from_score(score)
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
                "tide_score": tide_score_val,
                "cloud_cover": this_cloud_cover,
            }
        )

    # Store in cache and snapshot before returning
    generated_at = dj_timezone.now()
    ttl = int(getattr(settings, "FORECAST_CACHE_TTL", DEFAULT_FORECAST_CACHE_TTL))
    stale_ttl = int(
        getattr(settings, "FORECAST_CACHE_STALE_TTL", DEFAULT_FORECAST_STALE_TTL)
    )

    # Add cache jitter so workers don't all expire together and burst upstream.
    import random

    ttl = max(60, int(ttl * random.uniform(0.88, 1.12)))

    try:
        cache.set(cache_key, result, timeout=ttl)
        cache.set(stale_key, result, timeout=stale_ttl)
    except Exception as e:
        logger.debug("Failed to set forecast cache: key=%s error=%r", cache_key, e)

    return {
        "hours": result,
        "source": "api",
        "generated_at": generated_at,
        "next_refresh_at": generated_at + timedelta(seconds=stale_ttl),
        "is_stale": False,
    }


def _snapshot_payload_on_failure(
    snapshot_key: str,
    snapshot_hours: list[Hour],
    db_payload: dict,
    neg_key: str,
) -> dict:
    stale_cache = cache.get(snapshot_key + ":stale")
    if stale_cache is not None:
        return {
            "hours": stale_cache,
            "source": "stale_cache",
            "generated_at": None,
            "next_refresh_at": None,
            "is_stale": True,
        }
    if snapshot_hours:
        return {
            "hours": snapshot_hours,
            "source": "stale_snapshot",
            "generated_at": None,
            "next_refresh_at": None,
            "is_stale": True,
        }
    if db_payload["hours"]:
        return db_payload | {"source": "db_fallback", "is_stale": True}

    neg_ttl = int(getattr(settings, "FORECAST_CACHE_NEGATIVE_TTL", DEFAULT_FORECAST_NEGATIVE_TTL))
    cache.set(neg_key, True, timeout=neg_ttl)
    return {
        "hours": [],
        "source": "unavailable",
        "generated_at": None,
        "next_refresh_at": None,
        "is_stale": True,
    }


def fetch_forecast_payload(
    hours: int = 72,
    coordinates: dict | None = None,
    timezone_str: str | None = None,
    *,
    country_slug: str | None = None,
    city_slug: str | None = None,
    location: SnorkelLocation | None = None,
    allow_api: bool = True,
    snapshot_ttl: int | None = None,
) -> dict:
    """Return forecast hours and metadata."""
    if coordinates is None:
        coordinates = CARBONERAS
    if timezone_str is None:
        timezone_str = "Europe/Madrid"

    cache_key, stale_key, neg_key = _build_cache_keys(
        coordinates=coordinates, hours=hours, timezone_str=timezone_str
    )
    snapshot_key = _snapshot_key(
        coordinates=coordinates,
        hours=hours,
        country_slug=country_slug,
        city_slug=city_slug,
        location=location,
    )

    # Backoff if we recently saw a request error.
    if cache.get(neg_key):
        snapshot_hours, _, _ = _load_forecast_snapshot(snapshot_key)
        db_payload = _fallback_payload(hours, timezone_str, country_slug, city_slug)
        return _snapshot_payload_on_failure(snapshot_key, snapshot_hours, db_payload, neg_key)

    cached = cache.get(cache_key)
    if cached is not None:
        return {
            "hours": cached,
            "source": "cache",
            "generated_at": None,
            "next_refresh_at": None,
            "is_stale": False,
        }

    snapshot_hours, generated_at, next_refresh_at = _load_forecast_snapshot(snapshot_key)
    now = dj_timezone.now()
    snapshot_is_fresh = False
    if generated_at is not None and next_refresh_at is not None:
        snapshot_is_fresh = next_refresh_at > now

    if snapshot_hours:
        payload = {
            "hours": snapshot_hours,
            "source": "snapshot",
            "generated_at": generated_at,
            "next_refresh_at": next_refresh_at,
            "is_stale": not snapshot_is_fresh,
        }
        if snapshot_is_fresh or not allow_api:
            return payload

    # Serve from DB first before hitting API when allowed.
    db_payload = _fallback_payload(hours, timezone_str, country_slug, city_slug)
    if db_payload["hours"]:
        return db_payload

    if not allow_api:
        if snapshot_hours:
            return {
                "hours": snapshot_hours,
                "source": "stale_snapshot",
                "generated_at": generated_at,
                "next_refresh_at": next_refresh_at,
                "is_stale": True,
            }
        return db_payload

    try:
        payload = _api_fetch_hours(
            coordinates=coordinates,
            hours=hours,
            timezone_str=timezone_str,
            country_slug=country_slug,
            city_slug=city_slug,
            cache_key=cache_key,
            stale_key=stale_key,
            neg_key=neg_key,
        )
    except Exception as e:  # pragma: no cover - fallback coverage belongs to caller
        neg_ttl = int(
            getattr(settings, "FORECAST_CACHE_NEGATIVE_TTL", DEFAULT_FORECAST_NEGATIVE_TTL)
        )
        try:
            cache.set(neg_key, True, timeout=neg_ttl)
        except Exception:
            pass
        logger.warning("Forecast API path failed, using fallback: error=%r", e)
        return _snapshot_payload_on_failure(snapshot_key, snapshot_hours, db_payload, neg_key)

    if payload["hours"]:
        _save_forecast_snapshot(
            snapshot_key,
            coordinates=coordinates,
            timezone_str=timezone_str,
            country_slug=country_slug,
            city_slug=city_slug,
            location=location,
            hours=hours,
            payload=payload["hours"],
        )

    return payload


def fetch_forecast(
    hours: int = 72,
    coordinates: dict | None = None,
    timezone_str: str | None = None,
    *,
    country_slug: str | None = None,
    city_slug: str | None = None,
    location: SnorkelLocation | None = None,
    allow_api: bool = True,
) -> list[Hour]:
    """Return list of hours with snorkel suitability flag for any location."""
    payload = fetch_forecast_payload(
        hours=hours,
        coordinates=coordinates,
        timezone_str=timezone_str,
        country_slug=country_slug,
        city_slug=city_slug,
        location=location,
        allow_api=allow_api,
    )
    return payload.get("hours", [])
