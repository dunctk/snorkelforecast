from datetime import datetime
from dateutil import tz
from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import render

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
    
    context = {
        "location": location_data,
        "hours": hours,
        "summary": {
            "total_hours": total,
            "ok_count": ok_count,
            "percent_ok": percent_ok,
            "earliest_ok": earliest_ok,
            "latest_ok": latest_ok,
        },
        "timezone": local_tz.tzname(now),
    }
    return render(request, "conditions/location_forecast.html", context)


# Legacy view for backward compatibility (redirects to Carboneras)
def home(request: HttpRequest) -> HttpResponse:
    """Legacy home view - redirects to Carboneras forecast."""
    from django.shortcuts import redirect
    return redirect('location_forecast', country='spain', city='carboneras')
