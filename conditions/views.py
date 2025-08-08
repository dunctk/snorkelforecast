from datetime import datetime, timedelta
from collections import defaultdict
from io import BytesIO
import random

from dateutil import tz
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

from .snorkel import fetch_forecast

# Popular locations data - this could be moved to a database later
LOCATIONS = {
    "spain": {
        "carboneras": {
            "city": "Carboneras",
            "country": "Spain",
            "coordinates": {"lat": 36.997, "lon": -1.896},
            "description": "Pristine Mediterranean waters in Andalusia",
            "timezone": "Europe/Madrid",
        }
    },
    "greece": {
        "zakynthos": {
            "city": "Zakynthos",
            "country": "Greece",
            "coordinates": {"lat": 37.7900, "lon": 20.7334},
            "description": "Crystal clear Ionian Sea waters",
            "timezone": "Europe/Athens",
        },
        "santorini": {
            "city": "Santorini",
            "country": "Greece",
            "coordinates": {"lat": 36.3932, "lon": 25.4615},
            "description": "Volcanic island with unique underwater landscapes",
            "timezone": "Europe/Athens",
        },
    },
    "turkey": {
        "kas": {
            "city": "Kas",
            "country": "Turkey",
            "coordinates": {"lat": 36.2025, "lon": 29.6367},
            "description": "Turquoise coast with excellent visibility",
            "timezone": "Europe/Istanbul",
        }
    },
    "croatia": {
        "dubrovnik": {
            "city": "Dubrovnik",
            "country": "Croatia",
            "coordinates": {"lat": 42.6507, "lon": 18.0944},
            "description": "Historic Adriatic coastal city",
            "timezone": "Europe/Zagreb",
        }
    },
    "usa": {
        "maui": {
            "city": "Maui",
            "country": "USA",
            "coordinates": {"lat": 20.7984, "lon": -156.3319},
            "description": "Tropical Pacific paradise with coral reefs",
            "timezone": "Pacific/Honolulu",
        }
    },
}


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
            )
            location_data["current_sst"] = (
                forecast[0]["sea_surface_temperature"] if forecast else None
            )

            popular_locations.append(location_data)

    country_list = [
        {
            "slug": slug,
            "name": next(iter(cities.values())).get("country", slug.title()) if cities else slug.title(),
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


def countries_index(request: HttpRequest) -> HttpResponse:
    """Index page listing all available countries with counts and sample cities."""
    countries = []
    for country_slug, cities in LOCATIONS.items():
        # Derive display name from any city's country field
        country_name = next(iter(cities.values())).get("country", country_slug.title()) if cities else country_slug.title()
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


def location_forecast(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Display forecast for a specific location."""
    # Find the location data
    if country not in LOCATIONS or city not in LOCATIONS[country]:
        raise Http404("Location not found")

    location_data = LOCATIONS[country][city]
    location_data['country_slug'] = country
    location_data['city_slug'] = city
    coordinates = location_data["coordinates"]
    timezone_str = location_data["timezone"]

    # fetch hourly forecast data for this location
    all_hours = fetch_forecast(coordinates=coordinates, timezone_str=timezone_str)

    # filter out past hours
    local_tz = tz.gettz(timezone_str)
    now = datetime.now(tz=local_tz)
    hours = [h for h in all_hours if h["time"] >= now]

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
    for day, day_hours in days.items():
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
        "next_window": next_window,
        "tide_times": tide_times,
        "next_early_high_tide": next_early_high_tide,
    }
    return render(request, "conditions/location_forecast.html", context)


def location_tide_chart(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Render a simple 24-hour tide chart image for the given location."""
    if country not in LOCATIONS or city not in LOCATIONS[country]:
        raise Http404("Location not found")

    location = LOCATIONS[country][city]

    hours = fetch_forecast(
        hours=24,
        coordinates=location["coordinates"],
        timezone_str=location["timezone"],
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


def location_og_image(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Generate a social sharing image for a location."""
    if country not in LOCATIONS or city not in LOCATIONS[country]:
        raise Http404("Location not found")

    location = LOCATIONS[country][city]

    forecast = fetch_forecast(
        hours=1,
        coordinates=location["coordinates"],
        timezone_str=location["timezone"],
    )
    sst = forecast[0]["sea_surface_temperature"] if forecast else None
    wave = forecast[0]["wave_height"] if forecast else None
    wind = forecast[0]["wind_speed"] if forecast else None

    WIDTH, HEIGHT = 1200, 630
    SAFE = 60

    # Create a more dynamic, water-like background
    img = Image.new("RGB", (WIDTH, HEIGHT), "#003973")
    draw = ImageDraw.Draw(img)

    # Draw some random circles to simulate light refractions
    for _ in range(50):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        r = random.randint(10, 100)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 20))

    # Apply a blur to create a softer, more blended look
    img = img.filter(ImageFilter.GaussianBlur(radius=30))

    # Add a subtle vignette to draw focus to the center
    vignette = Image.new("L", (WIDTH, HEIGHT), 0)
    draw_v = ImageDraw.Draw(vignette)
    draw_v.ellipse(
        (-WIDTH * 0.1, -HEIGHT * 0.1, WIDTH * 1.1, HEIGHT * 1.1), fill=255
    )
    vignette = vignette.filter(ImageFilter.GaussianBlur(100))
    img = Image.composite(img, ImageEnhance.Brightness(img).enhance(0.8), vignette)

    draw = ImageDraw.Draw(img)

    FONT_DIR = "/usr/share/fonts/truetype/dejavu"
    try:
        font_huge = ImageFont.truetype(f"{FONT_DIR}/DejaVuSans-Bold.ttf", 90)
        font_big = ImageFont.truetype(f"{FONT_DIR}/DejaVuSans-Bold.ttf", 48)
        font_small = ImageFont.truetype(f"{FONT_DIR}/DejaVuSans.ttf", 36)
    except OSError:
        font_huge = ImageFont.load_default()
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    tagline = "SnorkelForecast.com"
    tagline_bbox = draw.textbbox((0, 0), tagline, font=font_small)
    w = tagline_bbox[2] - tagline_bbox[0]
    draw.text((WIDTH - w - SAFE, SAFE), tagline, font=font_small, fill="#FFFFFF")

    location_text = f"{location['city']}, {location['country']}"
    location_bbox = draw.textbbox((0, 0), location_text, font=font_huge)
    w = location_bbox[2] - location_bbox[0]
    h = location_bbox[3] - location_bbox[1]
    
    # Add a subtle drop shadow for better readability
    draw.text(
        ((WIDTH - w) / 2 + 5, HEIGHT * 0.3 - h / 2 + 5),
        location_text,
        font=font_huge,
        fill="#000000"
    )
    draw.text(
        ((WIDTH - w) / 2, HEIGHT * 0.3 - h / 2),
        location_text,
        font=font_huge,
        fill="#FFFFFF"
    )

    def metric_pill(label: str, value: float, unit: str, y_offset: int) -> int:
        text = f"{label}: {value:.1f} {unit}"
        bbox = draw.textbbox((0, 0), text, font=font_big)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        padding = 20
        box = [
            ((WIDTH - w) / 2 - padding, y_offset),
            ((WIDTH + w) / 2 + padding, y_offset + h + padding),
        ]
        draw.rounded_rectangle(box, radius=30, fill=(255, 255, 255, 50))
        draw.text(
            (box[0][0] + padding, y_offset + padding / 2),
            text,
            font=font_big,
            fill="#FFFFFF",
        )
        return int(box[1][1] + 30)

    metric_y = int(HEIGHT * 0.6)
    if sst is not None:
        metric_y = metric_pill("Sea Temp", sst, "°C", metric_y)
    if wave is not None:
        metric_y = metric_pill("Wave", wave, "m", metric_y)
    if wind is not None:
        metric_y = metric_pill("Wind", wind, "m/s", metric_y)

    output = BytesIO()
    img.save(output, "PNG", optimize=True)
    return HttpResponse(output.getvalue(), content_type="image/png")



# Legacy view for backward compatibility (redirects to Carboneras)
def home(request: HttpRequest) -> HttpResponse:
    """Legacy home view - redirects to Carboneras forecast."""
    from django.shortcuts import redirect

    return redirect("location_forecast", country="spain", city="carboneras")
