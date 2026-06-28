from datetime import datetime, timedelta
import logging
from collections import defaultdict
from io import BytesIO

from dateutil import tz
from django.core.cache import cache
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.conf import settings
from django.db.models import Avg, Count, Max, Q
from django.views.decorators.cache import cache_page
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils import timezone as django_timezone
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os
import math

from .snorkel import RATING_THRESHOLDS, THRESHOLDS, fetch_forecast, fetch_forecast_payload
from .models import ForecastHour, SnorkelLocation
from .history import (
    get_recent_averages,
    get_monthly_scores,
    get_monthly_sst,
)
from .locations import LOCATIONS
from .osm import osm_service
from .models_spots import OSMSpot, ImportTile

# Popular locations moved to conditions/locations.py


logger = logging.getLogger(__name__)


RANKING_MIN_UPCOMING_HOURS = 6
RANKING_MIN_HISTORICAL_HOURS = 24
RANKING_CACHE_TTL = getattr(settings, "RANKING_CACHE_TTL", 1800)
COUNTRY_PAGE_CACHE_TTL = getattr(settings, "COUNTRY_PAGE_CACHE_TTL", 1800)


def _rating_label(score: float | None) -> str:
    if score is None:
        return "No data"
    if score >= RATING_THRESHOLDS["excellent"]:
        return "Excellent"
    if score >= RATING_THRESHOLDS["good"]:
        return "Good"
    if score >= RATING_THRESHOLDS["fair"]:
        return "Fair"
    return "Poor"


def _ranking_location_url(country_slug: str, city_slug: str) -> str:
    return f"/{country_slug}/{city_slug}/"


def _ranking_cache_key(country_slug: str | None, include_countries: bool, historical_limit: int) -> str:
    scope = country_slug or "global"
    countries_flag = "with-countries" if include_countries else "no-countries"
    return f"best-snorkeling-rankings:v2:{scope}:{countries_flag}:h{historical_limit}"


def _build_best_snorkeling_rankings(
    country_slug: str | None = None,
    *,
    include_countries: bool = True,
    historical_limit: int = 80,
) -> dict[str, object]:
    """Build historical and 72-hour rankings from stored forecast rows."""
    now = django_timezone.now()
    next_72h = now + timedelta(hours=72)
    historical_cutoff = now - timedelta(days=365)

    location_filter = Q(location__isnull=False)
    if country_slug:
        location_filter &= Q(country_slug=country_slug)

    upcoming_rows = (
        ForecastHour.objects.filter(location_filter, time__gte=now, time__lte=next_72h)
        .values(
            "location_id",
            "location__name",
            "location__country",
            "location__country_slug",
            "location__city_slug",
            "location__description",
        )
        .annotate(
            avg_score=Avg("score"),
            best_score=Max("score"),
            sample_hours=Count("id"),
            ok_hours=Count("id", filter=Q(ok=True)),
            avg_wave=Avg("wave_height"),
            avg_wind=Avg("wind_speed"),
            avg_sst=Avg("sea_surface_temperature"),
        )
        .filter(sample_hours__gte=RANKING_MIN_UPCOMING_HOURS)
        .order_by("-avg_score", "-best_score", "location__name")
    )

    upcoming = []
    for row in upcoming_rows[:40]:
        sample_hours = int(row["sample_hours"] or 0)
        ok_hours = int(row["ok_hours"] or 0)
        avg_score = row["avg_score"]
        upcoming.append(
            {
                "location_id": row["location_id"],
                "name": row["location__name"],
                "country": row["location__country"],
                "country_slug": row["location__country_slug"],
                "city_slug": row["location__city_slug"],
                "description": row["location__description"],
                "url": _ranking_location_url(
                    row["location__country_slug"], row["location__city_slug"]
                ),
                "avg_score": avg_score,
                "best_score": row["best_score"],
                "score_percent": round((avg_score or 0) * 100),
                "best_score_percent": round((row["best_score"] or 0) * 100),
                "rating_label": _rating_label(avg_score),
                "ok_hours": ok_hours,
                "sample_hours": sample_hours,
                "ok_percent": round(ok_hours / sample_hours * 100) if sample_hours else 0,
                "avg_wave": row["avg_wave"],
                "avg_wind": row["avg_wind"],
                "avg_sst": row["avg_sst"],
            }
        )

    historical_rows = (
        ForecastHour.objects.filter(location_filter, time__gte=historical_cutoff, time__lt=now)
        .values(
            "location_id",
            "location__name",
            "location__country",
            "location__country_slug",
            "location__city_slug",
            "location__description",
        )
        .annotate(
            avg_score=Avg("score"),
            sample_hours=Count("id"),
            ok_hours=Count("id", filter=Q(ok=True)),
            avg_wave=Avg("wave_height"),
            avg_wind=Avg("wind_speed"),
            avg_sst=Avg("sea_surface_temperature"),
        )
        .filter(sample_hours__gte=RANKING_MIN_HISTORICAL_HOURS)
        .order_by("-avg_score", "location__name")
    )

    historical = []
    for row in historical_rows[:historical_limit]:
        sample_hours = int(row["sample_hours"] or 0)
        ok_hours = int(row["ok_hours"] or 0)
        avg_score = row["avg_score"]
        historical.append(
            {
                "location_id": row["location_id"],
                "name": row["location__name"],
                "country": row["location__country"],
                "country_slug": row["location__country_slug"],
                "city_slug": row["location__city_slug"],
                "description": row["location__description"],
                "url": _ranking_location_url(
                    row["location__country_slug"], row["location__city_slug"]
                ),
                "avg_score": avg_score,
                "score_percent": round((avg_score or 0) * 100),
                "rating_label": _rating_label(avg_score),
                "ok_hours": ok_hours,
                "sample_hours": sample_hours,
                "ok_percent": round(ok_hours / sample_hours * 100) if sample_hours else 0,
                "avg_wave": row["avg_wave"],
                "avg_wind": row["avg_wind"],
                "avg_sst": row["avg_sst"],
            }
        )

    countries = []
    if include_countries:
        country_rows = (
            ForecastHour.objects.filter(
                location__isnull=False,
                time__gte=historical_cutoff,
                time__lt=now,
            )
            .values("country_slug", "location__country")
            .annotate(avg_score=Avg("score"), sample_hours=Count("id"))
            .filter(sample_hours__gte=RANKING_MIN_HISTORICAL_HOURS)
            .order_by("-avg_score", "location__country")
        )
        for row in country_rows:
            countries.append(
                {
                    "slug": row["country_slug"],
                    "name": row["location__country"],
                    "url": f"/{row['country_slug']}/",
                    "score_percent": round((row["avg_score"] or 0) * 100),
                    "sample_hours": row["sample_hours"],
                }
            )

    return {
        "upcoming": upcoming,
        "historical": historical,
        "countries": countries,
        "generated_at": now,
        "historical_days": 365,
        "forecast_hours": 72,
    }


def get_best_snorkeling_rankings(
    country_slug: str | None = None,
    *,
    include_countries: bool = True,
    historical_limit: int = 80,
) -> dict[str, object]:
    """Return cached rankings, computing them on cache miss."""
    cache_key = _ranking_cache_key(country_slug, include_countries, historical_limit)
    rankings = cache.get(cache_key)
    if rankings is not None:
        return rankings

    rankings = _build_best_snorkeling_rankings(
        country_slug,
        include_countries=include_countries,
        historical_limit=historical_limit,
    )
    cache.set(cache_key, rankings, RANKING_CACHE_TTL)
    return rankings


def warm_best_snorkeling_ranking_cache(country_slugs: list[str] | None = None) -> None:
    """Precompute ranking blobs after scheduled forecast refreshes."""
    global_rankings = _build_best_snorkeling_rankings()
    cache.set(_ranking_cache_key(None, True, 80), global_rankings, RANKING_CACHE_TTL)

    if country_slugs is None:
        country_slugs = list(
            SnorkelLocation.objects.values_list("country_slug", flat=True).distinct()
        )

    for country_slug in country_slugs:
        rankings = _build_best_snorkeling_rankings(
            country_slug,
            include_countries=False,
            historical_limit=30,
        )
        cache.set(_ranking_cache_key(country_slug, False, 30), rankings, RANKING_CACHE_TTL)


def _current_sst_by_location_id(locations: list[SnorkelLocation]) -> dict[int, float | None]:
    """Return the nearest upcoming sea temperature for each location from DB history."""
    location_ids = [location.id for location in locations]
    if not location_ids:
        return {}

    rows = (
        ForecastHour.objects.filter(
            location_id__in=location_ids,
            time__gte=django_timezone.now(),
            sea_surface_temperature__isnull=False,
        )
        .order_by("location_id", "time")
        .values_list("location_id", "sea_surface_temperature")
    )

    current_sst: dict[int, float | None] = {}
    for location_id, sst in rows:
        current_sst.setdefault(location_id, sst)

    missing_locations = [location for location in locations if location.id not in current_sst]
    if not missing_locations:
        return current_sst

    country_slugs = {location.country_slug for location in missing_locations}
    city_slugs = {location.city_slug for location in missing_locations}
    legacy_rows = (
        ForecastHour.objects.filter(
            location__isnull=True,
            country_slug__in=country_slugs,
            city_slug__in=city_slugs,
            time__gte=django_timezone.now(),
            sea_surface_temperature__isnull=False,
        )
        .order_by("country_slug", "city_slug", "time")
        .values_list("country_slug", "city_slug", "sea_surface_temperature")
    )

    legacy_sst: dict[tuple[str, str], float | None] = {}
    for country_slug, city_slug, sst in legacy_rows:
        legacy_sst.setdefault((country_slug, city_slug), sst)

    for location in missing_locations:
        sst = legacy_sst.get((location.country_slug, location.city_slug))
        if sst is not None:
            current_sst[location.id] = sst
    return current_sst


def _location_type_label(location_type: str | None) -> str:
    labels = {
        "beach": "Beach",
        "cove": "Cove",
        "bay": "Bay",
        "island": "Island",
        "reef": "Reef",
        "dive_site": "Dive site",
        "marine_park": "Marine park",
        "other": "Spot",
    }
    return labels.get(location_type or "other", "Spot")


def _build_country_region_groups(cities: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for city in cities:
        region_name = city.get("region") or "Featured snorkeling areas"
        grouped[region_name].append(city)

    return [
        {
            "name": region_name,
            "spots": sorted(spots, key=lambda item: item["city"].lower()),
            "spot_count": len(spots),
        }
        for region_name, spots in sorted(grouped.items(), key=lambda item: item[0].lower())
    ]


def _build_country_sst_summary(cities: list[dict]) -> dict:
    values = [
        float(city["current_sst"])
        for city in cities
        if isinstance(city.get("current_sst"), int | float)
    ]
    if not values:
        return {"has_data": False, "count": 0, "avg": None, "min": None, "max": None}

    return {
        "has_data": True,
        "count": len(values),
        "avg": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
    }


@cache_page(getattr(settings, "CACHE_TTL", 300))
def homepage(request: HttpRequest) -> HttpResponse:
    """Homepage showing popular snorkeling locations."""
    popular_locations = []

    # Get popular locations from database
    popular_location_objects = list(SnorkelLocation.objects.filter(is_popular=True))
    current_sst = _current_sst_by_location_id(popular_location_objects)

    for location in popular_location_objects:
        location_data = {
            "name": location.name,
            "city": location.name,  # For template compatibility
            "country": location.country,
            "coordinates": location.coordinates_dict,
            "timezone": location.timezone,
            "description": location.description,
            "country_slug": location.country_slug,
            "city_slug": location.city_slug,
        }

        location_data["current_sst"] = current_sst.get(location.id)

        popular_locations.append(location_data)

    flag_emojis = {
        "spain": "🇪🇸",
        "greece": "🇬🇷",
        "turkey": "🇹🇷",
        "croatia": "🇭🇷",
        "usa": "🇺🇸",
    }

    # Get unique countries from popular locations
    countries_from_db = (
        SnorkelLocation.objects.filter(is_popular=True)
        .values_list("country_slug", "country")
        .distinct()
    )

    country_list = [
        {
            "slug": country_slug,
            "name": country_name,
            "emoji": flag_emojis.get(country_slug, ""),
        }
        for country_slug, country_name in countries_from_db
    ]
    country_list.sort(key=lambda c: c["name"].lower())

    # Real catalogue size (not the small hardcoded LOCATIONS dict) for the hero copy.
    country_count = SnorkelLocation.objects.values("country_slug").distinct().count()

    context = {
        "popular_locations": popular_locations,
        "country_count": country_count,
        "countries": country_list,
    }
    return render(request, "conditions/homepage.html", context)


@cache_page(COUNTRY_PAGE_CACHE_TTL)
def country_directory(request: HttpRequest, country: str) -> HttpResponse:
    """Country directory page listing supported locations in the country.

    Shows all cities we have presets for within the given country slug.
    """
    # Get locations for this country from database
    country_locations = list(SnorkelLocation.objects.filter(country_slug=country))

    if not country_locations:
        raise Http404("Country not found")

    # Prepare city list with optional current SST for quick glance
    cities = []
    current_sst = _current_sst_by_location_id(country_locations)
    for location in country_locations:
        data = {
            "name": location.name,
            "city": location.name,  # For template compatibility
            "country": location.country,
            "region": location.region,
            "coordinates": location.coordinates_dict,
            "timezone": location.timezone,
            "description": location.description,
            "location_type": location.location_type,
            "location_type_label": _location_type_label(location.location_type),
            "is_verified": location.is_verified,
            "is_popular": location.is_popular,
            "quality_score": location.quality_score,
            "country_slug": country,
            "city_slug": location.city_slug,
        }

        data["current_sst"] = current_sst.get(location.id)

        cities.append(data)

    # Get country name from first location
    country_name = country_locations[0].country
    cities.sort(
        key=lambda item: (
            not item.get("is_popular"),
            -(item.get("quality_score") or 0),
            item["city"].lower(),
        )
    )
    region_groups = _build_country_region_groups(cities)
    featured_locations = cities[:6]
    sst_summary = _build_country_sst_summary(cities)

    context = {
        "country_slug": country,
        "country_name": country_name,
        "cities": cities,
        "region_groups": region_groups,
        "featured_locations": featured_locations,
        "sst_summary": sst_summary,
        "rankings": get_best_snorkeling_rankings(
            country,
            include_countries=False,
            historical_limit=30,
        ),
        "is_country_page": True,
    }
    return render(request, "conditions/country.html", context)


@cache_page(getattr(settings, "CACHE_TTL", 300))
def best_snorkeling(request: HttpRequest) -> HttpResponse:
    """Editorial ranking page for the best snorkeling places worldwide."""
    rankings = get_best_snorkeling_rankings()
    context = {
        "rankings": rankings,
        "country_name": "the World",
        "country_slug": "",
        "is_country_page": False,
    }
    return render(request, "conditions/best_snorkeling.html", context)


@cache_page(getattr(settings, "CACHE_TTL", 300))
def countries_index(request: HttpRequest) -> HttpResponse:
    """Index page listing all available countries with counts and sample cities."""
    countries = []

    # Group locations by country
    from django.db.models import Count

    country_stats = (
        SnorkelLocation.objects.values("country_slug", "country")
        .annotate(city_count=Count("id"))
        .order_by("country")
    )

    for stat in country_stats:
        country_slug = stat["country_slug"]
        country_name = stat["country"]
        city_count = stat["city_count"]

        # Get sample cities for this country
        sample_locations = SnorkelLocation.objects.filter(country_slug=country_slug)[:3]
        city_list = [
            {
                "city": location.name,
                "city_slug": location.city_slug,
                "country_slug": country_slug,
                "description": location.description,
            }
            for location in sample_locations
        ]

        countries.append(
            {
                "slug": country_slug,
                "name": country_name,
                "city_count": city_count,
                "sample_cities": city_list,
            }
        )

    # Sort alphabetically by display name
    countries.sort(key=lambda c: c["name"].lower())

    return render(request, "conditions/countries.html", {"countries": countries})


def _save_forecast_history(country_slug: str, city_slug: str, hours: list[dict]) -> None:
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


def _parse_history_days(value: str | None) -> int:
    """Return a bounded whole-day history offset for chart browsing."""
    if not value:
        return 0
    try:
        days = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(days, 30))


def _forecast_rows_to_hours(rows: list[ForecastHour], timezone_str: str) -> list[dict]:
    """Convert stored forecast rows into the template's hourly record shape."""
    if not rows:
        return []

    local_tz = tz.gettz(timezone_str) or tz.tzutc()
    sea = [row.sea_level_height for row in rows]
    high_ix: set[int] = set()
    for i in range(1, len(sea) - 1):
        prev, now, nxt = sea[i - 1], sea[i], sea[i + 1]
        if None not in (prev, now, nxt) and now is not None and now > prev and now > nxt:
            high_ix.add(i)

    converted = []
    for i, row in enumerate(rows):
        wave = row.wave_height
        wind = row.wind_speed
        sst = row.sea_surface_temperature
        current = row.current_velocity
        wave_ok = wave is not None and wave <= THRESHOLDS["wave_height"]
        wind_ok = wind is not None and wind <= THRESHOLDS["wind_speed"]
        sst_ok = (
            sst is not None
            and THRESHOLDS["sea_surface_temperature"][0]
            <= sst
            <= THRESHOLDS["sea_surface_temperature"][1]
        )
        slack_ok = i in high_ix and current is not None and current <= THRESHOLDS["current_velocity"]
        converted.append(
            {
                "time": row.time.astimezone(local_tz),
                "ok": row.ok,
                "score": row.score,
                "rating": row.rating or "poor",
                "wave_height": wave,
                "wind_speed": wind,
                "air_temperature": None,
                "sea_surface_temperature": sst,
                "sea_level_height": row.sea_level_height,
                "current_velocity": current,
                "wave_ok": wave_ok,
                "wind_ok": wind_ok,
                "sst_ok": sst_ok,
                "slack_ok": slack_ok,
                "is_high_tide": i in high_ix,
                "light_ok": True,
            }
        )
    return converted


def _historical_chart_hours(
    *,
    location: SnorkelLocation | None,
    country_slug: str,
    city_slug: str,
    timezone_str: str,
    start_time: datetime,
    hours: int = 72,
) -> list[dict]:
    """Load stored hourly data for a shifted chart window."""
    end_time = start_time + timedelta(hours=hours)
    rows = ForecastHour.objects.filter(
        time__gte=start_time,
        time__lt=end_time,
    )
    if location is not None and location.pk:
        rows = rows.filter(location=location)
    else:
        rows = rows.filter(country_slug=country_slug, city_slug=city_slug)

    return _forecast_rows_to_hours(list(rows.order_by("time")), timezone_str)


def _count_blockers(hours: list[dict]) -> list[dict]:
    """Return top blocker metrics for a list of hourly records."""
    metrics: list[tuple[str, str]] = [
        ("Waves", "wave_ok"),
        ("Wind", "wind_ok"),
        ("Sea temperature", "sst_ok"),
        ("Tide/current", "slack_ok"),
        ("Darkness", "light_ok"),
    ]

    counts: list[dict] = []
    for label, key in metrics:
        bad = [
            h
            for h in hours
            if (h.get(key) is not None and not bool(h.get(key)) and h.get("score") is not None)
        ]
        if bad:
            counts.append({"label": label, "count": len(bad)})

    counts.sort(key=lambda item: item["count"], reverse=True)
    return counts[:3]


def _build_day_summaries(hours: list[dict], local_tz: tz.tzfile | None = None) -> list[dict]:
    """Build compact day cards for the planning layer."""
    days: dict = defaultdict(list)
    for h in hours:
        day = h["time"].date()
        days[day].append(h)

    summaries = []
    today_tz = local_tz or tz.tzutc()
    today = datetime.now(tz=today_tz).date()
    for day in sorted(days)[:3]:
        day_hours = days[day]
        ratings = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        for h in day_hours:
            rating = h.get("rating") or "poor"
            ratings[rating] = ratings.get(rating, 0) + 1

        for tier in ("excellent", "good", "fair", "poor"):
            if ratings[tier] > 0:
                status = tier
                break
        else:
            status = "poor"

        blockers = _count_blockers(day_hours)
        summaries.append(
            {
                "date": day,
                "label": day.strftime("%A"),
                "ratings": ratings,
                "status": status,
                "main_blocker": blockers[0]["label"] if blockers else "Good",
                "is_today": day == today,
                "sample_hours": len(day_hours),
            }
        )

    return summaries


def _best_available_hours(hours: list[dict], limit: int = 3) -> list[dict]:
    """Return the best-scoring future hours (used when no clean window exists)."""
    if not hours:
        return []

    candidate_hours = [
        hour
        for hour in hours
        if hour.get("light_ok") is not False
    ]
    if not candidate_hours:
        return []

    def sort_key(record: dict) -> tuple:
        score = record.get("score")
        score_value = -1.0 if score is None else float(score)
        return (score_value, record["time"])

    ranked = sorted(candidate_hours, key=sort_key, reverse=True)
    picks: list[dict] = []
    for hour in ranked:
        blockers = []
        if hour.get("wave_ok") is not None and not bool(hour.get("wave_ok")):
            blockers.append("waves")
        if hour.get("wind_ok") is not None and not bool(hour.get("wind_ok")):
            blockers.append("wind")
        if hour.get("sst_ok") is not None and not bool(hour.get("sst_ok")):
            blockers.append("sea temperature")
        if hour.get("slack_ok") is not None and not bool(hour.get("slack_ok")):
            blockers.append("tide/current")
        if hour.get("light_ok") is not None and not bool(hour.get("light_ok")):
            blockers.append("darkness")

        picks.append(
            {
                "time": hour["time"],
                "score": hour.get("score", 0.0),
                "status": hour.get("rating", "poor"),
                "blockers": blockers[:2],
            }
        )
        if len(picks) >= limit:
            break

    return picks


def _find_next_safe_window(hours: list[dict]) -> dict | None:
    """Find the next contiguous, future window of acceptable daytime hours."""
    candidate_hours = [
        hour
        for hour in hours
        if hour.get("light_ok") is not False
    ]

    for idx, h in enumerate(candidate_hours):
        if h.get("ok"):
            start = h["time"]
            end = start
            j = idx + 1
            while (
                j < len(candidate_hours)
                and candidate_hours[j].get("ok")
                and candidate_hours[j]["time"] - candidate_hours[j - 1]["time"] == timedelta(hours=1)
            ):
                end = candidate_hours[j]["time"]
                j += 1
            return {"start": start, "end": end}
    return None


def _format_best_window(hours: list[dict], next_window: dict | None) -> dict | None:
    """Return a compact next-window payload for the UI."""
    if not next_window:
        return None

    start = next_window.get("start")
    end = next_window.get("end")
    return {
        "start": start,
        "end": end,
        "duration_hours": None if not end or not start else int((end - start).total_seconds() / 3600),
        "label": "Good window" if end and end != start else "Best hour",
    }


def _build_location_condition_tiles(hours: list[dict], local_tz: tz.tzfile | None) -> dict:
    """Summarize the most useful same-day conditions for the page header."""
    fallback = {
        "sunrise": None,
        "sunrise_label": None,
        "sunset": None,
        "sunset_label": None,
        "water_temp": None,
        "max_air_temp": None,
        "sky_label": "Sky",
        "sky_label_es": "Cielo",
        "sky_detail": "No data",
        "sky_detail_es": "Sin datos",
        "cloud_cover": None,
    }
    if not hours:
        return fallback

    now = datetime.now(tz=local_tz or tz.tzutc())
    today_hours = [h for h in hours if h.get("time") and h["time"].date() == now.date()]
    display_hours = today_hours or hours[:24]
    nearest_hour = display_hours[0]

    sunrise = next((h.get("sunrise") for h in display_hours if h.get("sunrise")), None)
    sunset = next((h.get("sunset") for h in display_hours if h.get("sunset")), None)
    display_tz = local_tz or tz.tzutc()
    local_sunrise = sunrise.astimezone(display_tz) if sunrise else None
    local_sunset = sunset.astimezone(display_tz) if sunset else None
    water_values = [
        float(h["sea_surface_temperature"])
        for h in display_hours
        if isinstance(h.get("sea_surface_temperature"), int | float)
    ]
    air_values = [
        float(h["air_temperature"])
        for h in display_hours
        if isinstance(h.get("air_temperature"), int | float)
    ]
    cloud_cover = nearest_hour.get("cloud_cover")

    if isinstance(cloud_cover, int | float):
        cloud_value = round(float(cloud_cover))
        if cloud_value <= 30:
            sky_label = "Clear"
            sky_label_es = "Despejado"
        elif cloud_value <= 70:
            sky_label = "Partly cloudy"
            sky_label_es = "Parcialmente nublado"
        else:
            sky_label = "Cloudy"
            sky_label_es = "Nublado"
        sky_detail = f"{cloud_value}% cloud"
        sky_detail_es = f"{cloud_value}% nubes"
    else:
        sky_label = "Sky"
        sky_label_es = "Cielo"
        sky_detail = "No data"
        sky_detail_es = "Sin datos"

    return {
        **fallback,
        "sunrise": local_sunrise,
        "sunrise_label": local_sunrise.strftime("%H:%M") if local_sunrise else None,
        "sunset": local_sunset,
        "sunset_label": local_sunset.strftime("%H:%M") if local_sunset else None,
        "water_temp": water_values[0] if water_values else None,
        "max_air_temp": max(air_values) if air_values else None,
        "sky_label": sky_label,
        "sky_label_es": sky_label_es,
        "sky_detail": sky_detail,
        "sky_detail_es": sky_detail_es,
        "cloud_cover": cloud_cover,
    }


def _status_word(rating: str | None) -> str:
    """Normalize rating values into a short semantic label."""
    if rating in {"excellent", "good"}:
        return "Good"
    if rating == "fair":
        return "Fair"
    return "Poor"


def _build_chart_summaries(hours: list[dict]) -> dict[str, str]:
    """Build plain-English summaries for 24h chart sections."""
    if not hours:
        return {
            "score": "No score data is available for the next 24 hours yet.",
            "wave": "No wave-height trend data is available for the next 24 hours yet.",
            "wind": "No wind-speed trend data is available for the next 24 hours yet.",
            "tide": "No tide trend data is available for the next 24 hours yet.",
        }

    score_hours = [h for h in hours if isinstance(h.get("score"), int | float)]
    if score_hours:
        best_score_hour = max(score_hours, key=lambda h: h.get("score", 0.0))
        best_time = best_score_hour["time"].strftime("%a %H:%M")
        best_score = round(best_score_hour.get("score", 0.0), 2)
        good_hours = sum(1 for h in score_hours if _status_word(h.get("rating")) != "Poor")
        score_summary = (
            f"Best snorkel score is {best_score} around {best_time}; "
            f"{good_hours} of {len(score_hours)} hours are good, fair, or excellent."
        )
    else:
        score_summary = "No score data is available for the next 24 hours yet."

    wave_values = [
        float(h["wave_height"]) for h in hours if isinstance(h.get("wave_height"), int | float)
    ]
    if wave_values:
        waves_ok = sum(1 for value in wave_values if value <= THRESHOLDS["wave_height"])
        min_wave = min(wave_values)
        max_wave = max(wave_values)
        wave_summary = (
            f"{waves_ok}/{len(wave_values)} sampled hours stay at or below "
            f"{THRESHOLDS['wave_height']}m (range {round(min_wave, 2)}m to {round(max_wave, 2)}m)."
        )
    else:
        wave_summary = "No wave-height trend data is available for the next 24 hours yet."

    wind_values = [
        float(h["wind_speed"]) for h in hours if isinstance(h.get("wind_speed"), int | float)
    ]
    if wind_values:
        wind_ok = sum(1 for value in wind_values if value <= THRESHOLDS["wind_speed"])
        min_wind = min(wind_values)
        max_wind = max(wind_values)
        wind_summary = (
            f"Wind is at or below {THRESHOLDS['wind_speed']}m/s in "
            f"{wind_ok}/{len(wind_values)} sampled hours (range {round(min_wind, 2)} to {round(max_wind, 2)}m/s)."
        )
    else:
        wind_summary = "No wind-speed trend data is available for the next 24 hours yet."

    tide_values = [
        float(h["sea_level_height"]) for h in hours if isinstance(h.get("sea_level_height"), int | float)
    ]
    if tide_values:
        min_tide = min(tide_values)
        max_tide = max(tide_values)
        slack_count = sum(1 for h in hours if h.get("is_high_tide"))
        tide_summary = (
            f"Tides range from {round(min_tide, 2)}m to {round(max_tide, 2)}m; "
            f"{slack_count} of {len(hours)} hours are in or near peak slack windows."
        )
    else:
        tide_summary = "No tide trend data is available for the next 24 hours yet."

    return {
        "score": score_summary,
        "wave": wave_summary,
        "wind": wind_summary,
        "tide": tide_summary,
    }


@cache_page(getattr(settings, "LOCATION_PAGE_CACHE_TTL", getattr(settings, "CACHE_TTL", 300)))
def location_forecast(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Display forecast for a specific location."""
    # First try to find location in database (for dynamic locations)
    try:
        location = SnorkelLocation.objects.get(country_slug=country, city_slug=city)
        location_data = {
            "name": location.name,
            "country": location.country,
            "coordinates": location.coordinates_dict,
            "timezone": location.timezone,
            "description": location.description,
            "country_slug": country,
            "city_slug": city,
        }
        coordinates = location.coordinates_dict
        timezone_str = location.timezone
    except SnorkelLocation.DoesNotExist:
        # Fall back to hardcoded locations
        if country not in LOCATIONS or city not in LOCATIONS[country]:
            # Try to find location via OSM
            osm_locations = osm_service.search_locations(query=city, country=country, limit=5)

            if osm_locations:
                # Use the first match
                osm_data = osm_locations[0]
                location = osm_service.create_or_update_location(osm_data)
                location_data = {
                    "name": location.name,
                    "country": location.country,
                    "coordinates": location.coordinates_dict,
                    "timezone": location.timezone,
                    "description": location.description,
                    "country_slug": country,
                    "city_slug": city,
                }
                coordinates = location.coordinates_dict
                timezone_str = location.timezone
            else:
                raise Http404("Location not found")
        else:
            # Use hardcoded location
            location_data = LOCATIONS[country][
                city
            ].copy()  # Make a copy to avoid modifying original
            location_data["country_slug"] = country
            location_data["city_slug"] = city
            coordinates = location_data["coordinates"]
            timezone_str = location_data["timezone"]
            location = None  # No database location object for hardcoded locations

    # Fetch hourly forecast data for this location.
    forecast_payload = fetch_forecast_payload(
        coordinates=coordinates,
        timezone_str=timezone_str,
        country_slug=country,
        city_slug=city,
        location=location,
        allow_api=False,
    )
    all_hours = forecast_payload.get("hours", [])
    if not all_hours:
        logger.warning(
            "Empty forecast for %s/%s at coords=%s tz=%s",
            country,
            city,
            coordinates,
            timezone_str,
        )

    # The background scheduler persists forecast data every 30 min for all
    # locations. No need to write on every page view.

    # filter out past hours
    local_tz = tz.gettz(timezone_str)
    now = datetime.now(tz=local_tz)
    hours = [h for h in all_hours if h["time"] >= now]
    if not hours and all_hours:
        logger.info(
            "All forecast hours are in the past for %s/%s (now=%s, last=%s)",
            country,
            city,
            now,
            all_hours[-1]["time"] if all_hours else None,
        )

    hours_24 = hours[:24]
    chart_history_days = _parse_history_days(request.GET.get("history_days"))
    chart_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(
        days=chart_history_days
    )
    if chart_history_days:
        chart_hours = _historical_chart_hours(
            location=location,
            country_slug=country,
            city_slug=city,
            timezone_str=timezone_str,
            start_time=chart_start,
        )
    else:
        chart_hours = hours
    chart_hours_24 = chart_hours[:24]
    chart_end = chart_start + timedelta(hours=72)
    chart_window = {
        "history_days": chart_history_days,
        "is_historical": chart_history_days > 0,
        "start": chart_start,
        "end": chart_end,
        "previous_days": chart_history_days + 1,
        "next_days": max(chart_history_days - 1, 0),
        "has_data": bool(chart_hours),
    }
    forecast_updated = forecast_payload.get("generated_at") or now
    total = len(hours)
    ok_hours = [h for h in hours if h.get("ok")]
    ok_count = len(ok_hours)
    percent_ok = round(ok_count / total * 100) if total > 0 else 0
    rating_counts = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}

    for h in hours:
        rating = h.get("rating") or "poor"
        if rating in rating_counts:
            rating_counts[rating] += 1

    if ok_hours:
        earliest_ok = ok_hours[0]["time"]
        latest_ok = ok_hours[-1]["time"]
    else:
        earliest_ok = latest_ok = None

    next_window = _find_next_safe_window(hours)

    decision_summary = {
        "total_hours": total,
        "ok_count": ok_count,
        "percent_ok": percent_ok,
        "can_snorkel": bool(next_window),
        "primary_blockers": _count_blockers(hours),
        "next_window": _format_best_window(hours, next_window),
        "earliest_ok": earliest_ok,
        "latest_ok": latest_ok,
        "updated_at": forecast_updated,
        "forecast_source": forecast_payload.get("source", "unknown"),
        "forecast_source_label": str(
            forecast_payload.get("source", "unknown")
        ).replace("_", " ").title(),
        "is_stale": bool(forecast_payload.get("is_stale", False)),
        "next_refresh_at": forecast_payload.get("next_refresh_at"),
    }

    day_planner = _build_day_summaries(hours, local_tz=local_tz)
    condition_tiles = _build_location_condition_tiles(hours, local_tz)
    best_available = _best_available_hours(hours, limit=3)
    chart_summaries = _build_chart_summaries(chart_hours_24)
    tide_times = [h["time"] for h in hours if h.get("is_high_tide")]
    next_early_high_tide = next((t for t in tide_times if t.hour < 9), None)

    # Historical aggregates for seasonal insights
    if "location" in locals() and location:
        recent_averages = get_recent_averages(location)
        monthly_scores = get_monthly_scores(location)
        monthly_sst = get_monthly_sst(location)
    else:
        recent_averages = get_recent_averages(country, city)
        monthly_scores = get_monthly_scores(country, city)
        monthly_sst = get_monthly_sst(country, city)
    season_labels = [m["month"].strftime("%b") for m in monthly_scores]
    season_scores = [
        round(m["avg_score"], 2) if m["avg_score"] is not None else None for m in monthly_scores
    ]
    best_months = [
        m["month"].strftime("%B")
        for m in sorted(monthly_scores, key=lambda x: x["avg_score"] or 0, reverse=True)[:3]
        if m["avg_score"] is not None
    ]
    sst_labels = [m["month"].strftime("%b") for m in monthly_sst]
    sst_avg = [
        round(m["avg_sst"], 1) if m["avg_sst"] is not None else None for m in monthly_sst
    ]
    sst_min = [
        round(m["min_sst"], 1) if m["min_sst"] is not None else None for m in monthly_sst
    ]
    sst_max = [
        round(m["max_sst"], 1) if m["max_sst"] is not None else None for m in monthly_sst
    ]
    warmest_month = max(
        monthly_sst, key=lambda m: m["avg_sst"] or 0
    )["month"].strftime("%B") if any(m.get("avg_sst") for m in monthly_sst) else None
    warmest_temp = round(
        max(m["avg_sst"] for m in monthly_sst if m["avg_sst"] is not None), 1
    ) if any(m.get("avg_sst") for m in monthly_sst) else None
    coldest_month = min(
        monthly_sst, key=lambda m: m["avg_sst"] or 0
    )["month"].strftime("%B") if any(m.get("avg_sst") for m in monthly_sst) else None
    coldest_temp = round(
        min(m["avg_sst"] for m in monthly_sst if m["avg_sst"] is not None), 1
    ) if any(m.get("avg_sst") for m in monthly_sst) else None

    # Use the location object if available, otherwise create a compatible object
    if "location" in locals() and location:
        context_location = location
    else:
        # Create a mock location object for legacy compatibility
        class MockLocation:
            def __init__(self, data):
                self.name = data.get("name", data.get("city", ""))
                self.city = data.get("city", "")
                self.country = data.get("country", "")
                self.country_slug = data.get("country_slug", "")
                self.city_slug = data.get("city_slug", "")
                self.description = data.get("description", "")
                self.latitude = data.get("coordinates", {}).get("lat", 0)
                self.longitude = data.get("coordinates", {}).get("lon", 0)

        context_location = MockLocation(location_data)

    # Nearby spots in the same country for internal linking and discovery
    nearby_spots = list(
        SnorkelLocation.objects.filter(country_slug=country)
        .exclude(city_slug=city)
        .order_by("name")[:6]
    )
    nearby_locations = []
    nearby_status_by_id: dict[int, str] = {}
    nearby_ids = [spot.id for spot in nearby_spots[:4]]
    if nearby_ids:
        nearby_rows = (
            ForecastHour.objects.filter(
                location_id__in=nearby_ids,
                time__gte=django_timezone.now(),
            )
            .order_by("location_id", "time")
            .values_list("location_id", "ok", "rating")
        )
        first_rating_by_id: dict[int, str] = {}
        for location_id, ok, rating in nearby_rows:
            first_rating_by_id.setdefault(location_id, rating or "poor")
            if ok:
                nearby_status_by_id[location_id] = "good"

        for location_id, rating in first_rating_by_id.items():
            nearby_status_by_id.setdefault(location_id, rating)

    for spot in nearby_spots[:4]:
        nearby_status = "unknown"
        if spot.id in nearby_status_by_id:
            nearby_status = nearby_status_by_id[spot.id]

        nearby_locations.append(
            {
                "name": spot.name,
                "city_slug": spot.city_slug,
                "country_slug": spot.country_slug,
                "description": spot.description,
                "status": nearby_status,
            }
        )

    context = {
        "location": context_location,
        "nearby_locations": nearby_locations,
        "forecast_source": forecast_payload.get("source", "unknown"),
        "forecast_is_stale": bool(forecast_payload.get("is_stale", False)),
        "forecast_refreshed_at": forecast_payload.get("generated_at"),
        "forecast_next_refresh_at": forecast_payload.get("next_refresh_at"),
        "hours": hours,
        "hours_24": hours_24,
        "chart_hours": chart_hours,
        "chart_hours_24": chart_hours_24,
        "chart_window": chart_window,
        "summary": decision_summary,
        "decision_summary": decision_summary,
        "day_planner": day_planner,
        "condition_tiles": condition_tiles,
        "best_available": best_available,
        "chart_summaries": chart_summaries,
        "rating_counts": rating_counts,
        "timezone": local_tz.tzname(now),
        "next_window": next_window,
        "tide_times": tide_times,
        "next_early_high_tide": next_early_high_tide,
        "recent_averages": recent_averages,
        "season_labels": season_labels,
        "season_scores": season_scores,
        "best_months": best_months,
        "sst_labels": sst_labels,
        "sst_avg": sst_avg,
        "sst_min": sst_min,
        "sst_max": sst_max,
        "warmest_month": warmest_month,
        "warmest_temp": warmest_temp,
        "coldest_month": coldest_month,
        "coldest_temp": coldest_temp,
    }
    return render(request, "conditions/location_forecast.html", context)


def location_search(request: HttpRequest) -> HttpResponse:
    """Location search and discovery page."""
    query = request.GET.get("q", "").strip()
    location_type = request.GET.get("type", "")
    country = request.GET.get("country", "")

    locations = []
    search_performed = False

    if query or location_type or country:
        search_performed = True

        # Search in database first (for existing locations)
        db_locations = SnorkelLocation.objects.all()

        if query:
            db_locations = db_locations.filter(name__icontains=query)
        if location_type:
            db_locations = db_locations.filter(location_type=location_type)
        if country:
            db_locations = db_locations.filter(country__icontains=country)

        # Convert to common format
        for loc in db_locations[:20]:  # Limit results
            locations.append(
                {
                    "name": loc.name,
                    "country": loc.country,
                    "country_slug": loc.country_slug,
                    "city_slug": loc.city_slug,
                    "location_type": loc.location_type,
                    "description": loc.description,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "source": "database",
                    "is_popular": loc.is_popular,
                }
            )

        # If no results from database, try OSM search
        if not locations and query:
            osm_results = osm_service.search_locations(query=query, limit=10)

            for osm_loc in osm_results:
                # Check if we already have this location
                existing = SnorkelLocation.objects.filter(
                    osm_id=osm_loc["osm_id"], osm_type=osm_loc["osm_type"]
                ).first()

                if existing:
                    locations.append(
                        {
                            "name": existing.name,
                            "country": existing.country,
                            "country_slug": existing.country_slug,
                            "city_slug": existing.city_slug,
                            "location_type": existing.location_type,
                            "description": existing.description,
                            "latitude": existing.latitude,
                            "longitude": existing.longitude,
                            "source": "database",
                            "is_popular": existing.is_popular,
                        }
                    )
                else:
                    locations.append(
                        {
                            "name": osm_loc["name"],
                            "country": osm_loc["country"],
                            "country_slug": osm_loc["country_slug"],
                            "city_slug": osm_loc["city_slug"],
                            "location_type": osm_loc["location_type"],
                            "description": osm_loc["description"],
                            "latitude": osm_loc["latitude"],
                            "longitude": osm_loc["longitude"],
                            "source": "osm",
                            "is_popular": False,
                        }
                    )

    # Get location type options for filter
    location_types = [
        ("beach", "Beaches"),
        ("cove", "Coves"),
        ("bay", "Bays"),
        ("island", "Islands"),
        ("reef", "Reefs"),
        ("dive_site", "Dive Sites"),
        ("marine_park", "Marine Parks"),
    ]

    context = {
        "query": query,
        "location_type": location_type,
        "country_filter": country,
        "locations": locations,
        "search_performed": search_performed,
        "location_types": location_types,
        "result_count": len(locations),
    }

    return render(request, "conditions/location_search.html", context)


@cache_page(getattr(settings, "CACHE_TTL", 300))
def guides_index(request: HttpRequest) -> HttpResponse:
    """Hub page listing all evergreen snorkeling guides."""
    from .guides import get_guides

    return render(request, "conditions/guides_index.html", {"guides": get_guides()})


@cache_page(getattr(settings, "CACHE_TTL", 300))
def guide_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Render a single evergreen snorkeling guide, with a few popular spots."""
    from .guides import get_guide

    guide = get_guide(slug)
    if not guide:
        raise Http404("Guide not found")

    popular = list(
        SnorkelLocation.objects.filter(is_popular=True).values(
            "name", "city_slug", "country_slug", "country"
        )[:8]
    )
    return render(
        request,
        "conditions/guide_detail.html",
        {"guide": guide, "popular_locations": popular},
    )


def indexnow_key_file(request: HttpRequest, key: str) -> HttpResponse:
    """Serve the IndexNow key verification file at /<key>.txt.

    IndexNow requires a text file at the host root, named <key>.txt and
    containing exactly the key, to prove ownership before accepting URL pings.
    """
    expected = getattr(settings, "INDEXNOW_KEY", "")
    if not expected or key != expected:
        raise Http404("Not found")
    return HttpResponse(expected, content_type="text/plain")


def health_check(request: HttpRequest) -> HttpResponse:
    """Health check endpoint with OSM import status for Docker and monitoring."""
    from django.db import connection
    from django.core.cache import cache
    from datetime import datetime

    # Test database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "error"

    # Test cache
    try:
        cache.set("health_check", "ok", 10)
        cache_status = "ok" if cache.get("health_check") == "ok" else "error"
    except Exception:
        cache_status = "error"

    # Get location counts
    legacy_count = SnorkelLocation.objects.count()
    osm_count = OSMSpot.objects.count()
    total_locations = legacy_count + osm_count

    # Get OSM import status
    tiles_pending = ImportTile.objects.filter(status="pending").count()
    tiles_running = ImportTile.objects.filter(status="running").count()
    tiles_done = ImportTile.objects.filter(status="done").count()
    tiles_failed = ImportTile.objects.filter(status="failed").count()

    # Overall status
    status = "ok" if db_status == "ok" and cache_status == "ok" else "error"

    return JsonResponse(
        {
            "status": status,
            "database": db_status,
            "cache": cache_status,
            "locations": {
                "total": total_locations,
                "legacy": legacy_count,
                "osm": osm_count,
            },
            "osm_import": {
                "tiles_pending": tiles_pending,
                "tiles_running": tiles_running,
                "tiles_done": tiles_done,
                "tiles_failed": tiles_failed,
            },
            "timestamp": datetime.now().isoformat(),
        },
        status=200 if status == "ok" else 503,
    )


def location_search_api(request: HttpRequest) -> HttpResponse:
    """API endpoint for location search with autocomplete."""
    query = request.GET.get("q", "")
    if isinstance(query, list):
        query = query[0]

    results = defaultdict(list)

    if not query:
        return JsonResponse(results)

    query = query.lower()

    # Search locations in database
    matching_locations = SnorkelLocation.objects.filter(name__icontains=query)[:20]  # Limit results

    for location in matching_locations:
        results[location.country].append(
            {
                "city": location.name,
                "slug": location.city_slug,
                "country_slug": location.country_slug,
            }
        )

    return JsonResponse(results)


@cache_page(getattr(settings, "CACHE_TTL", 300))
def location_tide_chart(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Render a simple 24-hour tide chart image for the given location."""
    try:
        location = SnorkelLocation.objects.get(country_slug=country, city_slug=city)
    except SnorkelLocation.DoesNotExist:
        raise Http404("Location not found")

    # Use the default 72h horizon so thumbnail requests reuse the same cache key
    # warmed by forecast pages and the scheduler, instead of causing separate
    # Open-Meteo calls for a 24h-only cache entry.
    hours = fetch_forecast(
        coordinates=location.coordinates_dict,
        timezone_str=location.timezone,
        country_slug=country,
        city_slug=city,
    )[:24]

    if not hours:
        raise Http404("No tide data")

    heights = [h["sea_level_height"] for h in hours]
    if all(h is None for h in heights):
        raise Http404("No tide data")

    heights = [h if h is not None else 0 for h in heights]

    width, height_img = 600, 200
    margin = 10
    y_min, y_max = min(heights), max(heights)
    if y_min == y_max:
        y_max = y_min + 1

    x_step = (width - 2 * margin) / (len(heights) - 1)
    y_scale = (height_img - 2 * margin) / (y_max - y_min)

    points = [
        (
            margin + i * x_step,
            height_img - margin - (h - y_min) * y_scale,
        )
        for i, h in enumerate(heights)
    ]

    # Transparent background with the bioluminescent-aqua accent so the chart
    # blends onto the glass cards in every theme (day / twilight / night).
    img = Image.new("RGBA", (width, height_img), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    polygon = points + [
        (points[-1][0], height_img - margin),
        (points[0][0], height_img - margin),
    ]
    draw.polygon(polygon, fill=(91, 224, 200, 38))  # translucent aqua fill
    draw.line(points, fill=(91, 224, 200, 255), width=3, joint="curve")  # aqua stroke

    output = BytesIO()
    img.save(output, "PNG")
    return HttpResponse(output.getvalue(), content_type="image/png")


@cache_page(getattr(settings, "CACHE_TTL", 300))
def location_og_image(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Generate a high-contrast social sharing image for a location.

    Focus on large, readable typography and strong contrast. Avoid
    semi-transparent light-on-light elements to keep text legible in
    previews across platforms.
    """
    try:
        location = SnorkelLocation.objects.get(country_slug=country, city_slug=city)
    except SnorkelLocation.DoesNotExist:
        raise Http404("Location not found")

    # Intentionally do not include live metrics on OG images; keep them
    # stable and descriptive for social previews.

    WIDTH, HEIGHT = 1200, 630
    SAFE = 64

    # Background: deep ocean gradient
    grad = Image.new("RGB", (1, HEIGHT))
    top = (6, 78, 118)  # darker teal
    bottom = (2, 44, 67)
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        grad.putpixel((0, y), (r, g, b))
    img = grad.resize((WIDTH, HEIGHT))

    # Add subtle wave texture as focal background
    texture = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(texture)
    amplitude = 10
    spacing = 26
    for y0 in range(int(HEIGHT * 0.25), int(HEIGHT * 0.9), spacing):
        points = []
        for x in range(0, WIDTH + 1, 8):
            y = y0 + amplitude * math.sin((x / 80.0) + (y0 / 50.0))
            points.append((x, y))
        tdraw.line(points, fill=(173, 216, 230, 35), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), texture).convert("RGB")

    # Subtle vignette for focus
    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    draw_v = ImageDraw.Draw(vignette)
    draw_v.ellipse(
        (-int(WIDTH * 0.2), -int(HEIGHT * 0.3), int(WIDTH * 1.2), int(HEIGHT * 1.3)), fill=255
    )
    vignette = vignette.filter(ImageFilter.GaussianBlur(120))
    img = Image.composite(img, ImageEnhance.Brightness(img).enhance(0.85), vignette)

    draw = ImageDraw.Draw(img)

    FONT_DIR = "/usr/share/fonts/truetype/dejavu"
    try:
        font_small = ImageFont.truetype(f"{FONT_DIR}/DejaVuSans.ttf", 46)
    except OSError:
        font_small = ImageFont.load_default()

    # Brand tag top-left
    brand = "SnorkelForecast.com"
    draw.text((SAFE, SAFE), brand, font=font_small, fill="#E0F2FE")

    # Location title with automatic fit
    base_font_size = 220
    location_text = f"{location.name}, {location.country}"

    def fit_font(size: int) -> ImageFont.FreeTypeFont:
        try:
            return ImageFont.truetype(f"{FONT_DIR}/DejaVuSans-Bold.ttf", size)
        except OSError:
            return ImageFont.load_default()

    font_title = fit_font(base_font_size)
    max_width = WIDTH - SAFE * 2
    while True:
        bbox = draw.textbbox((0, 0), location_text, font=font_title)
        w = bbox[2] - bbox[0]
        if w <= max_width or (
            hasattr(font_title, "size") and getattr(font_title, "size", 20) <= 80
        ):
            break
        # reduce and retry
        new_size = max(80, int((getattr(font_title, "size", base_font_size)) * 0.9))
        font_title = fit_font(new_size)

    # Dark plate behind title for readability (centered)
    bbox = draw.textbbox((0, 0), location_text, font=font_title)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    tx = (WIDTH - w) // 2
    ty = int(HEIGHT * 0.34) - h // 2
    plate_pad_x, plate_pad_y = 48, 32
    plate = [
        (tx - plate_pad_x, ty - plate_pad_y),
        (tx + w + plate_pad_x, ty + h + plate_pad_y),
    ]
    # Semi-transparent overlay behind the title for extra contrast
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    odraw.rounded_rectangle(plate, radius=28, fill=(6, 36, 58, 210))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    # Title on top
    draw.text((tx, ty), location_text, font=font_title, fill="#F8FAFC")

    # Horizontal metrics row with icons below the title
    include_values_env = str(os.getenv("OG_INCLUDE_VALUES", "false")).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    include_values = include_values_env or (
        request.GET.get("values", "").lower() in {"1", "true", "yes", "on"}
    )

    wave_val = wind_val = sst_val = None
    if include_values:
        try:
            forecast = fetch_forecast(
                hours=1,
                coordinates=location.coordinates_dict,
                timezone_str=location.timezone,
                country_slug=country,
                city_slug=city,
            )
        except Exception:  # pragma: no cover - OG image should still render
            forecast = None
        if forecast:
            sst_val = forecast[0].get("sea_surface_temperature")
            wave_val = forecast[0].get("wave_height")
            wind_ms = forecast[0].get("wind_speed")
            wind_val = wind_ms * 3.6 if isinstance(wind_ms, (int, float)) else None

    items = []
    if include_values:
        items = [
            ("Waves", f"{wave_val:.1f} m" if isinstance(wave_val, (int, float)) else "—"),
            ("Wind", f"{wind_val:.0f} km/h" if isinstance(wind_val, (int, float)) else "—"),
            ("Water", f"{sst_val:.0f}°C" if isinstance(sst_val, (int, float)) else "—"),
            ("Daylight", "High"),
        ]
    else:
        items = [
            ("Waves", "height"),
            ("Wind", "speed"),
            ("Water", "temp"),
            ("Daylight", "visibility"),
        ]

    # Build pill widths to center the row
    gap = 24
    pills = []
    for label, value in items:
        text = f"{label}: {value}"
        tb = draw.textbbox((0, 0), text, font=font_small)
        tw = tb[2] - tb[0]
        ph = tb[3] - tb[1]
        pw = tw + 48 + 20  # icon space + padding
        pills.append((text, pw, ph))
    total_w = sum(pw for _, pw, _ in pills) + gap * (len(pills) - 1)
    start_x = (WIDTH - total_w) // 2
    row_y = ty + h + 60

    # Draw a semi-transparent strip behind the pills
    strip = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(strip)
    sdraw.rounded_rectangle(
        [
            (start_x - 24, row_y - 18),
            (start_x + total_w + 24, row_y + max(ph for _, _, ph in pills) + 18),
        ],
        radius=22,
        fill=(6, 36, 58, 160),
    )
    img = Image.alpha_composite(img.convert("RGBA"), strip).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Draw pills
    cx = start_x
    icon_colors = ["#7DD3FC", "#FDE68A", "#FCA5A5", "#86EFAC"]
    for idx, (text, pw, ph) in enumerate(pills):
        draw.rounded_rectangle([(cx, row_y), (cx + pw, row_y + ph + 10)], radius=16, fill="#063245")
        # icon circle
        icon_r = 18
        cy = row_y + (ph + 10) // 2
        draw.ellipse(
            [(cx + 16, cy - icon_r), (cx + 16 + 2 * icon_r, cy + icon_r)],
            fill=icon_colors[idx % len(icon_colors)],
        )
        # text
        draw.text((cx + 16 + 2 * icon_r + 12, row_y + 6), text, font=font_small, fill="#F8FAFC")
        cx += pw + gap

    # Brand small at bottom-right
    brand = "SnorkelForecast.com"
    bb = draw.textbbox((0, 0), brand, font=font_small)
    bx = WIDTH - SAFE - (bb[2] - bb[0])
    by = HEIGHT - SAFE - (bb[3] - bb[1])
    draw.rounded_rectangle(
        [(bx - 14, by - 8), (WIDTH - SAFE + 14, by + (bb[3] - bb[1]) + 8)],
        radius=14,
        fill="#063245",
    )
    draw.text((bx, by), brand, font=font_small, fill="#E0F2FE")

    output = BytesIO()
    img.save(output, "PNG", optimize=True)
    return HttpResponse(output.getvalue(), content_type="image/png")


@cache_page(getattr(settings, "CACHE_TTL", 300))
def site_og_image(request: HttpRequest) -> HttpResponse:
    """Generate a site-wide OG image with strong, readable branding."""
    WIDTH, HEIGHT = 1200, 630
    SAFE = 64

    # Gradient background (darker for contrast)
    top = (8, 122, 175)
    bottom = (2, 44, 67)
    grad = Image.new("RGB", (1, HEIGHT))
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        grad.putpixel((0, y), (r, g, b))
    img = grad.resize((WIDTH, HEIGHT))

    # Vignette
    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    draw_v = ImageDraw.Draw(vignette)
    draw_v.ellipse(
        (-int(WIDTH * 0.2), -int(HEIGHT * 0.3), int(WIDTH * 1.2), int(HEIGHT * 1.3)), fill=255
    )
    vignette = vignette.filter(ImageFilter.GaussianBlur(120))
    img = Image.composite(img, ImageEnhance.Brightness(img).enhance(0.85), vignette)

    draw = ImageDraw.Draw(img)

    FONT_DIR = "/usr/share/fonts/truetype/dejavu"
    try:
        font_huge = ImageFont.truetype(f"{FONT_DIR}/DejaVuSans-Bold.ttf", 164)
        font_big = ImageFont.truetype(f"{FONT_DIR}/DejaVuSans.ttf", 52)
    except OSError:
        font_huge = ImageFont.load_default()
        font_big = ImageFont.load_default()

    # Centered title
    title = "SnorkelForecast"
    tb = draw.textbbox((0, 0), title, font=font_huge)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    tx = (WIDTH - tw) // 2
    ty = int(HEIGHT * 0.38) - th // 2
    draw.rounded_rectangle(
        [(tx - 36, ty - 24), (tx + tw + 36, ty + th + 24)], radius=30, fill="#06243A"
    )
    draw.text((tx, ty), title, font=font_huge, fill="#F8FAFC")

    # Tagline centered
    tagline = "Snorkeling forecasts worldwide"
    tbb = draw.textbbox((0, 0), tagline, font=font_big)
    draw.text(
        ((WIDTH - (tbb[2] - tbb[0])) // 2, ty + th + 36), tagline, font=font_big, fill="#E0F2FE"
    )

    # Add subtle wave texture
    texture = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(texture)
    amplitude = 10
    spacing = 26
    for y0 in range(int(HEIGHT * 0.25), int(HEIGHT * 0.9), spacing):
        points = []
        for x in range(0, WIDTH + 1, 8):
            y = y0 + amplitude * math.sin((x / 80.0) + (y0 / 50.0))
            points.append((x, y))
        tdraw.line(points, fill=(173, 216, 230, 55), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), texture).convert("RGB")

    # Brand small bottom-right
    brand = "SnorkelForecast.com"
    bb = draw.textbbox((0, 0), brand, font=font_big)
    bx = WIDTH - SAFE - (bb[2] - bb[0])
    by = HEIGHT - SAFE - (bb[3] - bb[1])
    draw.rounded_rectangle(
        [(bx - 14, by - 8), (WIDTH - SAFE + 14, by + (bb[3] - bb[1]) + 8)],
        radius=14,
        fill="#063245",
    )
    draw.text((bx, by), brand, font=font_big, fill="#E0F2FE")

    output = BytesIO()
    img.save(output, "PNG", optimize=True)
    return HttpResponse(output.getvalue(), content_type="image/png")


# Legacy view for backward compatibility (redirects to Carboneras)
def home(request: HttpRequest) -> HttpResponse:
    """Legacy home view - redirects to Carboneras forecast."""
    from django.shortcuts import redirect

    return redirect("location_forecast", country="spain", city="carboneras")


@cache_page(getattr(settings, "CACHE_TTL", 300))
def location_history_api(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Return recent historical data for a location as JSON (last 7 days)."""
    import json
    from datetime import timedelta
    from django.utils import timezone as djtz

    if not SnorkelLocation.objects.filter(country_slug=country, city_slug=city).exists():
        raise Http404("Location not found")

    since = djtz.now() - timedelta(days=7)
    qs = (
        ForecastHour.objects.filter(country_slug=country, city_slug=city, time__gte=since)
        .order_by("time")
        .values(
            "time",
            "ok",
            "rating",
            "score",
            "wave_height",
            "wind_speed",
            "sea_surface_temperature",
            "sea_level_height",
            "current_velocity",
        )
    )
    data = []
    for r in qs:
        r = dict(r)
        t = r.get("time")
        if hasattr(t, "isoformat"):
            r["time"] = t.isoformat()
        data.append(r)
    return HttpResponse(
        json.dumps({"country": country, "city": city, "data": data}),
        content_type="application/json",
    )


@cache_page(getattr(settings, "CACHE_TTL", 300))
def location_history(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Simple page showing historical trend for the last 7 days."""
    try:
        location = SnorkelLocation.objects.get(country_slug=country, city_slug=city)
    except SnorkelLocation.DoesNotExist:
        raise Http404("Location not found")

    return render(
        request,
        "conditions/history.html",
        {
            "country_slug": country,
            "city_slug": city,
            "location": location,
        },
    )


@cache_page(getattr(settings, "CACHE_TTL", 300))
def location_sea_temperature(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Dedicated sea temperature page for a location."""
    try:
        location = SnorkelLocation.objects.get(country_slug=country, city_slug=city)
        location_data = {
            "name": location.name,
            "country": location.country,
            "coordinates": location.coordinates_dict,
            "timezone": location.timezone,
            "description": location.description,
            "country_slug": country,
            "city_slug": city,
        }
        coordinates = location.coordinates_dict
        timezone_str = location.timezone
    except SnorkelLocation.DoesNotExist:
        if country not in LOCATIONS or city not in LOCATIONS[country]:
            osm_locations = osm_service.search_locations(query=city, country=country, limit=5)
            if osm_locations:
                osm_data = osm_locations[0]
                location = osm_service.create_or_update_location(osm_data)
                location_data = {
                    "name": location.name,
                    "country": location.country,
                    "coordinates": location.coordinates_dict,
                    "timezone": location.timezone,
                    "description": location.description,
                    "country_slug": country,
                    "city_slug": city,
                }
                coordinates = location.coordinates_dict
                timezone_str = location.timezone
            else:
                raise Http404("Location not found")
        else:
            location_data = LOCATIONS[country][city].copy()
            location_data["country_slug"] = country
            location_data["city_slug"] = city
            coordinates = location_data["coordinates"]
            timezone_str = location_data["timezone"]
            location = None

    forecast_payload = fetch_forecast_payload(
        coordinates=coordinates,
        timezone_str=timezone_str,
        country_slug=country,
        city_slug=city,
        location=location,
        allow_api=False,
    )
    all_hours = forecast_payload.get("hours", [])

    current_sst = None
    current_wave = None
    current_wind = None
    if all_hours:
        current = all_hours[0]
        current_sst = current.get("sea_surface_temperature")
        current_wave = current.get("wave_height")
        current_wind = current.get("wind_speed")

    if "location" in locals() and location:
        recent_averages = get_recent_averages(location)
        monthly_sst = get_monthly_sst(location, months=24)
    else:
        recent_averages = get_recent_averages(country, city)
        monthly_sst = get_monthly_sst(country, city, months=24)

    sst_labels = [m["month"].strftime("%b") for m in monthly_sst]
    sst_avg = [
        round(m["avg_sst"], 1) if m["avg_sst"] is not None else None for m in monthly_sst
    ]
    sst_min = [
        round(m["min_sst"], 1) if m["min_sst"] is not None else None for m in monthly_sst
    ]
    sst_max = [
        round(m["max_sst"], 1) if m["max_sst"] is not None else None for m in monthly_sst
    ]
    warmest_month = max(
        monthly_sst, key=lambda m: m["avg_sst"] or 0
    )["month"].strftime("%B") if any(m.get("avg_sst") for m in monthly_sst) else None
    warmest_temp = round(
        max(m["avg_sst"] for m in monthly_sst if m["avg_sst"] is not None), 1
    ) if any(m.get("avg_sst") for m in monthly_sst) else None
    coldest_month = min(
        monthly_sst, key=lambda m: m["avg_sst"] or 0
    )["month"].strftime("%B") if any(m.get("avg_sst") for m in monthly_sst) else None
    coldest_temp = round(
        min(m["avg_sst"] for m in monthly_sst if m["avg_sst"] is not None), 1
    ) if any(m.get("avg_sst") for m in monthly_sst) else None

    if "location" in locals() and location:
        context_location = location
    else:
        class MockLocation:
            def __init__(self, data):
                self.name = data.get("name", data.get("city", ""))
                self.city = data.get("city", "")
                self.country = data.get("country", "")
                self.country_slug = data.get("country_slug", "")
                self.city_slug = data.get("city_slug", "")
                self.description = data.get("description", "")
                self.latitude = data.get("coordinates", {}).get("lat", 0)
                self.longitude = data.get("coordinates", {}).get("lon", 0)

        context_location = MockLocation(location_data)

    nearby_locations = list(
        SnorkelLocation.objects.filter(country_slug=country)
        .exclude(city_slug=city)
        .values("name", "city_slug", "country_slug", "description")[:6]
    )

    context = {
        "location": context_location,
        "nearby_locations": nearby_locations,
        "current_sst": current_sst,
        "current_wave": current_wave,
        "current_wind": current_wind,
        "recent_averages": recent_averages,
        "sst_labels": sst_labels,
        "sst_avg": sst_avg,
        "sst_min": sst_min,
        "sst_max": sst_max,
        "warmest_month": warmest_month,
        "warmest_temp": warmest_temp,
        "coldest_month": coldest_month,
        "coldest_temp": coldest_temp,
    }
    return render(request, "conditions/location_sea_temperature.html", context)


@cache_page(getattr(settings, "CACHE_TTL", 300))
@xframe_options_exempt
def location_sea_temperature_embed(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Minimal embeddable sea-temperature chart for iframe widgets."""
    try:
        location = SnorkelLocation.objects.get(country_slug=country, city_slug=city)
        location_data = {
            "name": location.name,
            "country": location.country,
            "coordinates": location.coordinates_dict,
            "timezone": location.timezone,
            "country_slug": country,
            "city_slug": city,
        }
        coordinates = location.coordinates_dict
    except SnorkelLocation.DoesNotExist:
        if country not in LOCATIONS or city not in LOCATIONS[country]:
            raise Http404("Location not found")
        location_data = LOCATIONS[country][city].copy()
        location_data["country_slug"] = country
        location_data["city_slug"] = city
        coordinates = location_data["coordinates"]
        location = None

    forecast_payload = fetch_forecast_payload(
        coordinates=coordinates,
        timezone_str=location_data.get("timezone", "UTC"),
        country_slug=country,
        city_slug=city,
        location=location,
        allow_api=False,
    )
    all_hours = forecast_payload.get("hours", [])
    current_sst = all_hours[0].get("sea_surface_temperature") if all_hours else None

    if location:
        monthly_sst = get_monthly_sst(location, months=24)
    else:
        monthly_sst = get_monthly_sst(country, city, months=24)

    context = {
        "location_country": location_data.get("country", ""),
        "location_name": location_data.get("name", location_data.get("city", "")),
        "country_slug": country,
        "city_slug": city,
        "current_sst": current_sst,
        "sst_labels": [m["month"].strftime("%b") for m in monthly_sst],
        "sst_avg": [round(m["avg_sst"], 1) if m["avg_sst"] is not None else None for m in monthly_sst],
        "sst_min": [round(m["min_sst"], 1) if m["min_sst"] is not None else None for m in monthly_sst],
        "sst_max": [round(m["max_sst"], 1) if m["max_sst"] is not None else None for m in monthly_sst],
    }
    return render(request, "conditions/embed_sea_temperature.html", context)
