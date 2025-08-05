# SnorkelForecast.com

> **MVP – v0.1 (Carboneras‑only)**

A minimal Django 5.0 web‑app that queries the free, key‑less **Open‑Meteo Marine & Weather APIs** and shows whether the next few days in Carboneras, Spain meet “perfect snorkelling” thresholds.

---

## 1  User story

| Role                                                     | Goal                                                                                           | Benefit                                                           |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| **George** – 34‑year‑old British expat living in Almería | *“See at a glance which hours in the next three days are good for snorkelling in Carboneras.”* | Spends less time scanning surf reports and more time in the water |

### Acceptance criteria

1. Landing page loads at **`https://snorkelforecast.com/`**.
2. Shows a simple 72‑hour chart or table where each hour is coloured **green** (ideal) or **grey** (not ideal).
3. Uses George’s local timezone (Europe/Madrid).
4. Hard‑codes Carboneras (lat 36.997 N, lon ‑1.896 E) for the MVP, but latitude/longitude can be passed as query params in the future.
5. Deployable on fly.io / Railway with zero database setup.

---

## 2  Project structure

```
.
├─ snorkelforecast/          # Django project
│   ├─ settings.py
│   ├─ urls.py
│   └─ wsgi.py
├─ conditions/              # Django app
│   ├─ views.py
│   ├─ snorkel.py           # business logic
│   └─ templates/
│       └─ conditions/
│           └─ index.html
├─ static/
│   ├─ src/input.css        # Tailwind directives
│   └─ css/output.css       # built file (ignored in VCS)
├─ pyproject.toml           # uv‑managed deps
├─ ruff.toml
└─ README.md (this file)
```

---

## 3  Dependencies (`pyproject.toml` – managed by **uv**)

```toml
[project]
name = "snorkelforecast"
version = "0.1.0"
description = "Carboneras snorkelling forecast using Open‑Meteo"
requires-python = ">=3.12"

[project.dependencies]
Django = "^5.0.3"
httpx = "^0.27.0"
python-dateutil = "^2.9.0"
whitenoise = "^6.6.0"            # serve static in prod

[project.optional-dependencies]
dev = [
  "ruff>=0.4.0",
]

[build-system]
requires = ["uv>=0.1.35"]
build-backend = "uv.build"
```

### Install (dev)

```bash
curl https://sh.uv | sh                     # 1 – install uv
uv venv                                      # 2 – create venv
uv pip install -r <(uv pip compile)          # 3 – install deps
```

---

## 4  Ruff config (`ruff.toml`)

```toml
line-length = 100
select = ["E", "F", "I", "UP", "B", "D"]
ignore = ["D105"]          # allow missing docstring in magic methods
```

Lint all files:

```bash
uv run ruff check .
```

---

## 5  Tailwind CSS (CLI‑only)

```bash
# 1 – Install Tailwind standalone binary (no Node toolchain)
curl -sLo tailwind https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.4/tailwindcss-linux-x64 && chmod +x tailwind

# 2 – Build once (CI) or in watch‑mode (dev)
./tailwind -i static/src/input.css -o static/css/output.css --minify
```

`static/src/input.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

Add `WhitenoiseMiddleware` after `SecurityMiddleware` in `settings.py` and set `STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"` for production.

---

## 6  Business logic (`conditions/snorkel.py`)

```python
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
}

class Hour(TypedDict):
    time: datetime
    ok: bool


def fetch_forecast(hours: int = 72) -> list[Hour]:
    """Return list of hours with snorkel suitability flag (Carboneras only)."""
    marine_url = (
        "https://marine-api.open-meteo.com/v1/marine"
        f"?latitude={CARBONERAS['lat']}&longitude={CARBONERAS['lon']}"
        "&hourly=wave_height,sea_surface_temperature"
        "&timezone=UTC"
        f"&past_hours=0&forecast_hours={hours}"
    )
    wx_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={CARBONERAS['lat']}&longitude={CARBONERAS['lon']}"
        "&hourly=wind_speed_10m"
        "&timezone=UTC"
        f"&past_hours=0&forecast_hours={hours}"
    )
    with httpx.Client(timeout=10.0) as client:
        marine, wx = client.get(marine_url).json(), client.get(wx_url).json()

    # Assume identical time arrays
    times_utc = [datetime.fromisoformat(t).replace(tzinfo=timezone.utc) for t in marine["hourly"]["time"]]
    local = tz.gettz("Europe/Madrid")

    result: list[Hour] = []
    for i, t in enumerate(times_utc):
        wave = marine["hourly"]["wave_height"][i]
        sst = marine["hourly"]["sea_surface_temperature"][i]
        wind = wx["hourly"]["wind_speed_10m"][i]

        ok = (
            wave is not None and wave <= THRESHOLDS["wave_height"] and
            wind is not None and wind <= THRESHOLDS["wind_speed"] and
            sst is not None and THRESHOLDS["sea_surface_temperature"][0] <= sst <= THRESHOLDS["sea_surface_temperature"][1]
        )
        result.append({"time": t.astimezone(local), "ok": ok})
    return result
```

---

## 7  View + template (`conditions/views.py` & `index.html`)

```python
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .snorkel import fetch_forecast


def home(request: HttpRequest) -> HttpResponse:
    hours = fetch_forecast()
    return render(request, "conditions/index.html", {"hours": hours})
```

`templates/conditions/index.html`

```django
{% load static %}
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Carboneras Snorkel Forecast</title>
    <link href="{% static 'css/output.css' %}" rel="stylesheet">
  </head>
  <body class="bg-sky-50 min-h-screen flex flex-col items-center p-4">
    <h1 class="text-2xl font-bold mb-4">Snorkel Forecast – Carboneras</h1>

    <div class="grid grid-cols-6 sm:grid-cols-12 gap-1 text-xs">
      {% for h in hours %}
        <div class="p-2 rounded {{ 'bg-emerald-400' if h.ok else 'bg-gray-300' }}">
          <time datetime="{{ h.time|date:'c' }}">
            {{ h.time|date:'D&nbsp;H:i' }}
          </time>
        </div>
      {% endfor %}
    </div>
  </body>
</html>
```

---

## 8  Django settings additions

```python
INSTALLED_APPS += ["conditions"]
MIDDLEWARE += ["whitenoise.middleware.WhiteNoiseMiddleware"]
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # for collectstatic
```

Add route in `urls.py`:

```python
from django.urls import path, include
from conditions.views import home

urlpatterns = [
    path("", home, name="home"),
]
```

---

## 9  Run locally

```bash
./tailwind -i static/src/input.css -o static/css/output.css --watch &
uv run python manage.py runserver 8000
```

Navigate to [http://localhost:8000](http://localhost:8000) – green blocks are your snorkel windows!

---

## 10  Deploy

1. `uv pip install gunicorn`
2. `python manage.py collectstatic --noinput`
3. `gunicorn snorkelforecast.wsgi:application`

Use **fly.io** or **Railway** (both can run a container with no DB).

---

### Next steps

* Allow arbitrary lat/lon via GET params → multi‑spot support.
* Cache API responses (Redis or file cache).
* Replace heuristics with visibility + tide when available.

---

© 2025 SnorkelForecast.com – MIT Licence

