from datetime import datetime, timedelta
from collections import defaultdict
from io import BytesIO

from dateutil import tz
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from PIL import Image, ImageDraw, ImageFont

from .snorkel import fetch_forecast

# Popular locations data - this could be moved to a database later
LOCATIONS = {
    "spain": {
        "carboneras": {
            "city": "Carboneras",
            "country": "Spain", 
            "coordinates": {"lat": 36.997, "lon": -1.896},
            "description": "Pristine Mediterranean waters in Andalusia",
            "timezone": "Europe/Madrid"
        }
    },
    "greece": {
        "zakynthos": {
            "city": "Zakynthos",
            "country": "Greece",
            "coordinates": {"lat": 37.7900, "lon": 20.7334},
            "description": "Crystal clear Ionian Sea waters",
            "timezone": "Europe/Athens"
        },
        "santorini": {
            "city": "Santorini", 
            "country": "Greece",
            "coordinates": {"lat": 36.3932, "lon": 25.4615},
            "description": "Volcanic island with unique underwater landscapes",
            "timezone": "Europe/Athens"
        }
    },
    "turkey": {
        "kas": {
            "city": "Kas",
            "country": "Turkey",
            "coordinates": {"lat": 36.2025, "lon": 29.6367},
            "description": "Turquoise coast with excellent visibility",
            "timezone": "Europe/Istanbul"
        }
    },
    "croatia": {
        "dubrovnik": {
            "city": "Dubrovnik",
            "country": "Croatia", 
            "coordinates": {"lat": 42.6507, "lon": 18.0944},
            "description": "Historic Adriatic coastal city",
            "timezone": "Europe/Zagreb"
        }
    },
    "usa": {
        "maui": {
            "city": "Maui",
            "country": "USA",
            "coordinates": {"lat": 20.7984, "lon": -156.3319},
            "description": "Tropical Pacific paradise with coral reefs",
            "timezone": "Pacific/Honolulu"
        }
    }
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
    
    context = {
        "popular_locations": popular_locations
    }
    return render(request, "conditions/homepage.html", context)


def location_forecast(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Display forecast for a specific location."""
    # Find the location data
    if country not in LOCATIONS or city not in LOCATIONS[country]:
        raise Http404("Location not found")
    
    location_data = LOCATIONS[country][city]
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

    image_url = request.build_absolute_uri(
        reverse("location_og_image", args=[country, city])
    )

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
        "timezone": local_tz.tzname(now),
        "day_summaries": day_summaries,
        "next_window": next_window,
        "tide_times": tide_times,
        "next_early_high_tide": next_early_high_tide,
        "og_image_url": image_url,
    }
    return render(request, "conditions/location_forecast.html", context)


def location_og_image(request: HttpRequest, country: str, city: str) -> HttpResponse:
    """Generate a simple social sharing image for a location."""
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

    width, height = 1200, 630
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    top = (3, 105, 161)
    bottom = (14, 165, 233)
    for y in range(height):
        ratio = y / height
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    try:
        font_large = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80
        )
        font_medium = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40
        )
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30
        )
    except OSError:
        font_large = font_medium = font_small = ImageFont.load_default()

    draw.text((60, 40), "SnorkelForecast.com", font=font_small, fill="white")
    draw.text(
        (60, 180),
        f"{location['city']}, {location['country']}",
        font=font_large,
        fill="white",
    )

    y_info = 300
    if sst is not None:
        draw.text((60, y_info), f"Sea Temp: {sst:.1f}°C", font=font_medium, fill="white")
        y_info += 60
    if wave is not None:
        draw.text((60, y_info), f"Wave: {wave:.1f} m", font=font_medium, fill="white")
        y_info += 60
    if wind is not None:
        draw.text((60, y_info), f"Wind: {wind:.1f} m/s", font=font_medium, fill="white")

    draw.rectangle([(0, 0), (width - 1, height - 1)], outline="white", width=8)

    output = BytesIO()
    img.save(output, format="PNG")
    return HttpResponse(output.getvalue(), content_type="image/png")


# Legacy view for backward compatibility (redirects to Carboneras)
def home(request: HttpRequest) -> HttpResponse:
    """Legacy home view - redirects to Carboneras forecast."""
    from django.shortcuts import redirect
    return redirect('location_forecast', country='spain', city='carboneras')
