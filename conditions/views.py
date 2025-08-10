from datetime import datetime, timedelta
import logging
from collections import defaultdict
from io import BytesIO

from dateutil import tz
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.cache import cache_page
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import math

from .snorkel import fetch_forecast
from .models import ForecastHour
from .history import save_forecast_history
from .locations import LOCATIONS

# Popular locations moved to conditions/locations.py


logger = logging.getLogger(__name__)


@cache_page(getattr(settings, "CACHE_TTL", 300))
def homepage(request: HttpRequest) -> HttpResponse:
    """Homepage showing popular snorkeling locations."""
    popular_locations = []
    for country_slug, cities in LOCATIONS.items():
        for city_slug, location_data in cities.items():
            location_data["country_slug"] = country_slug
            location_data["city_slug"] = city_slug

            # Fetch current sea surface temperature for each location
            forecast = fetch_forecast(
                hours=1,
                coordinates=location_data["coordinates"],
                timezone_str=location_data["timezone"],
                country_slug=country_slug,
                city_slug=city_slug,
            )
            if not forecast:
                logger.warning(
                    "No forecast returned for homepage location: %s, %s",
                    location_data.get("country"),
                    location_data.get("city"),
                )
            location_data["current_sst"] = (
                forecast[0]["sea_surface_temperature"] if forecast else None
            )

            popular_locations.append(location_data)

    country_list = [
        {
            "slug": slug,
            "name": next(iter(cities.values())).get("country", slug.title())
            if cities
            else slug.title(),
        }
        for slug, cities in LOCATIONS.items()
    ]
    country_list.sort(key=lambda c: c["name"].lower())

    context = {
        "popular_locations": popular_locations,
        "country_count": len(LOCATIONS),
        "countries": country_list,
    }
    return render(request, "conditions/homepage.html", context)


@cache_page(getattr(settings, "CACHE_TTL", 300))
def country_directory(request: HttpRequest, country: str) -> HttpResponse:
    """Country directory page listing supported locations in the country.

    Shows all cities we have presets for within the given country slug.
    """
    if country not in LOCATIONS:
        raise Http404("Country not found")

    # Prepare city list with optional current SST for quick glance
    cities = []
    for city_slug, location_data in LOCATIONS[country].items():
        data = dict(location_data)
        data["country_slug"] = country
        data["city_slug"] = city_slug

        forecast = fetch_forecast(
            hours=1,
            coordinates=data["coordinates"],
            timezone_str=data["timezone"],
            country_slug=country,
            city_slug=city_slug,
        )
        if not forecast:
            logger.warning(
                "No forecast returned for country page location: %s/%s",
                country,
                city_slug,
            )
        data["current_sst"] = forecast[0]["sea_surface_temperature"] if forecast else None

        cities.append(data)

    # Derive nice country label from first entry (they all share same country name)
    country_name = next(iter(LOCATIONS[country].values())).get("country", country.title())

    context = {
        "country_slug": country,
        "country_name": country_name,
        "cities": cities,
    }
    return render(request, "conditions/country.html", context)


@cache_page(getattr(settings, "CACHE_TTL", 300))
def countries_index(request: HttpRequest) -> HttpResponse:
    """Index page listing all available countries with counts and sample cities."""
    countries = []
    for country_slug, cities in LOCATIONS.items():
        # Derive display name from any city's country field
        country_name = (
            next(iter(cities.values())).get("country", country_slug.title())
            if cities
            else country_slug.title()
        )
        city_list = [
            {
                "city": data.get("city", city_slug.title()),
                "city_slug": city_slug,
                "country_slug": country_slug,
                "description": data.get("description"),
            }
            for city_slug, data in cities.items()
        ]
        countries.append(
            {
                "slug": country_slug,
                "name": country_name,
                "city_count": len(city_list),
                "sample_cities": city_list[:3],
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


@cache_page(getattr(settings, "CACHE_TTL", 300))
def location_forecast(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Display forecast for a specific location."""
    # Find the location data
    if country not in LOCATIONS or city not in LOCATIONS[country]:
        raise Http404("Location not found")

    location_data = LOCATIONS[country][city]
    location_data["country_slug"] = country
    location_data["city_slug"] = city
    coordinates = location_data["coordinates"]
    timezone_str = location_data["timezone"]

    # fetch hourly forecast data for this location
    all_hours = fetch_forecast(
        coordinates=coordinates,
        timezone_str=timezone_str,
        country_slug=country,
        city_slug=city,
    )
    if not all_hours:
        logger.warning(
            "Empty forecast for %s/%s at coords=%s tz=%s",
            country,
            city,
            coordinates,
            timezone_str,
        )

    # Persist for historical analysis
    save_forecast_history(country, city, all_hours)

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

    # first 24 hours for separate charts
    hours_24 = hours[:24]

    # compute summary statistics
    total = len(hours)
    ok_hours = [h for h in hours if h.get("ok")]
    ok_count = len(ok_hours)
    percent_ok = round(ok_count / total * 100) if total > 0 else 0

    # rating breakdown
    rating_counts = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
    for h in hours:
        rating = h.get("rating") or "poor"
        if rating in rating_counts:
            rating_counts[rating] += 1

    # determine earliest and latest suitable times
    if ok_hours:
        earliest_ok = ok_hours[0]["time"]
        latest_ok = ok_hours[-1]["time"]
    else:
        earliest_ok = latest_ok = None

    # group hours by date to highlight best periods
    days = defaultdict(list)
    for h in hours:
        days[h["time"].date()].append(h)

    day_summaries = []
    daily_outlook = []
    for day, day_hours in days.items():
        ok_day = [h for h in day_hours if h.get("ok")]
        # Build per-day rating breakdown and top-tier window (always shown)
        counts = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
        for h in day_hours:
            r = h.get("rating") or "poor"
            if r in counts:
                counts[r] += 1

        # Determine the best available rating for the day
        order = ["excellent", "good", "fair", "poor"]
        top_rating = next((r for r in order if counts[r] > 0), "poor")

        # Find earliest and latest continuous block for the top rating
        top_times = [h["time"] for h in day_hours if h.get("rating") == top_rating]
        top_start = top_end = None
        if top_times:
            top_start = top_times[0]
            top_end = top_times[0]
            # Walk through consecutive hours to extend the initial block
            for i in range(1, len(top_times)):
                if top_times[i] - top_times[i - 1] == timedelta(hours=1):
                    top_end = top_times[i]
                else:
                    break

        daily_outlook.append(
            {
                "date": day,
                "label": (
                    ok_day[0]["time"].strftime("%A")
                    if ok_day
                    else day_hours[0]["time"].strftime("%A")
                ),
                "counts": counts,
                "top_rating": top_rating,
                "top_start": top_start,
                "top_end": top_end,
            }
        )

        # Compute only when there are suitable 'ok' hours for best-period blurb
        ok_day = [h for h in day_hours if h.get("ok")]
        if not ok_day:
            continue
        day_earliest = ok_day[0]["time"]
        day_latest = ok_day[-1]["time"]
        if day_latest.hour < 12:
            period = "morning"
        elif day_earliest.hour >= 12:
            period = "afternoon"
        else:
            period = "morning and afternoon"
        day_summaries.append(
            {
                "date": day,
                "label": day_earliest.strftime("%A"),
                "period": period,
                "earliest": day_earliest,
                "latest": day_latest,
            }
        )

    # find next continuous block of suitable conditions
    next_window = None
    for idx, h in enumerate(hours):
        if h.get("ok"):
            start = h["time"]
            end = start
            j = idx + 1
            while (
                j < len(hours)
                and hours[j].get("ok")
                and hours[j]["time"] - hours[j - 1]["time"] == timedelta(hours=1)
            ):
                end = hours[j]["time"]
                j += 1
            next_window = {"start": start, "end": end}
            break
    tide_times = [h["time"] for h in hours if h.get("is_high_tide")]
    next_early_high_tide = next((t for t in tide_times if t.hour < 9), None)

    context = {
        "location": location_data,
        "hours": hours,
        "hours_24": hours_24,
        "summary": {
            "total_hours": total,
            "ok_count": ok_count,
            "percent_ok": percent_ok,
            "earliest_ok": earliest_ok,
            "latest_ok": latest_ok,
        },
        "rating_counts": rating_counts,
        "timezone": local_tz.tzname(now),
        "day_summaries": day_summaries,
        "daily_outlook": sorted(daily_outlook, key=lambda d: d["date"]),
        "next_window": next_window,
        "tide_times": tide_times,
        "next_early_high_tide": next_early_high_tide,
    }
    return render(request, "conditions/location_forecast.html", context)


@cache_page(getattr(settings, "CACHE_TTL", 300))
def location_tide_chart(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Render a simple 24-hour tide chart image for the given location."""
    if country not in LOCATIONS or city not in LOCATIONS[country]:
        raise Http404("Location not found")

    location = LOCATIONS[country][city]

    hours = fetch_forecast(
        hours=24,
        coordinates=location["coordinates"],
        timezone_str=location["timezone"],
        country_slug=country,
        city_slug=city,
    )

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

    img = Image.new("RGB", (width, height_img), "#EFF6FF")
    draw = ImageDraw.Draw(img)

    polygon = points + [
        (points[-1][0], height_img - margin),
        (points[0][0], height_img - margin),
    ]
    draw.polygon(polygon, fill="#BFDBFE")
    draw.line(points, fill="#2563EB", width=4)

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
    if country not in LOCATIONS or city not in LOCATIONS[country]:
        raise Http404("Location not found")

    location = LOCATIONS[country][city]

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
        tdraw.line(points, fill=(173, 216, 230, 55), width=2)
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
        font_big = ImageFont.truetype(f"{FONT_DIR}/DejaVuSans-Bold.ttf", 64)
        font_small = ImageFont.truetype(f"{FONT_DIR}/DejaVuSans.ttf", 44)
    except OSError:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Brand tag top-left
    brand = "SnorkelForecast.com"
    draw.text((SAFE, SAFE), brand, font=font_small, fill="#E0F2FE")

    # Location title with automatic fit
    base_font_size = 180
    location_text = f"{location['city']}, {location['country']}"

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
    ty = int(HEIGHT * 0.38) - h // 2
    plate_pad_x, plate_pad_y = 40, 26
    plate = [
        (tx - plate_pad_x, ty - plate_pad_y),
        (tx + w + plate_pad_x, ty + h + plate_pad_y),
    ]
    draw.rounded_rectangle(plate, radius=28, fill="#06243A")
    draw.text((tx, ty), location_text, font=font_title, fill="#F8FAFC")

    # Descriptive blurb with simple icons (centered)
    desc_lines = [
        ("Waves", "height"),
        ("Wind", "speed"),
        ("Water temp", "comfort"),
        ("Daylight", "visibility"),
    ]
    # Compute block height
    line_h = draw.textbbox((0, 0), "Ag", font=font_small)[3]
    block_h = len(desc_lines) * (line_h + 10) - 10
    y0 = int(HEIGHT * 0.62) - block_h // 2
    icon_size = 14
    for i, (k, v) in enumerate(desc_lines):
        text = f"{k} · {v}"
        tb = draw.textbbox((0, 0), text, font=font_small)
        tw = tb[2] - tb[0]
        x_text = (WIDTH - tw) // 2 + 24
        y_line = y0 + i * (line_h + 10)
        # simple circle icon to the left
        draw.ellipse(
            [
                (x_text - 24, y_line + line_h // 2 - icon_size // 2),
                (x_text - 24 + icon_size, y_line + line_h // 2 + icon_size // 2),
            ],
            fill="#7DD3FC",
        )
        draw.text((x_text, y_line), text, font=font_small, fill="#E0F2FE")

    # Brand small at top-right
    brand = "SnorkelForecast.com"
    bb = draw.textbbox((0, 0), brand, font=font_small)
    bx = WIDTH - SAFE - (bb[2] - bb[0])
    by = SAFE
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

    if country not in LOCATIONS or city not in LOCATIONS[country]:
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
    if country not in LOCATIONS or city not in LOCATIONS[country]:
        raise Http404("Location not found")

    location = LOCATIONS[country][city]
    return render(
        request,
        "conditions/history.html",
        {
            "country_slug": country,
            "city_slug": city,
            "location": location,
        },
    )
