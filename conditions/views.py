from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .snorkel import fetch_forecast


def home(request: HttpRequest) -> HttpResponse:
    hours = fetch_forecast()
    return render(request, "conditions/index.html", {"hours": hours})
