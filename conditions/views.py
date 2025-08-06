from datetime import datetime

from dateutil import tz
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .snorkel import fetch_forecast


def home(request: HttpRequest) -> HttpResponse:
    # fetch hourly forecast data
    all_hours = fetch_forecast()
    # filter out past hours
    local_tz = tz.gettz("Europe/Madrid")
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
    return render(request, "conditions/index.html", context)
