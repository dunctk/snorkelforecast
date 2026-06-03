from __future__ import annotations

import os
import signal
import sys
import time

import django


def _setup_django() -> None:
    # DJANGO_SETTINGS_MODULE is set in startup.sh; fallback for local runs
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snorkelforecast.snorkelforecast.settings")
    django.setup()


def _iter_locations():
    # Import lazily after Django setup
    from .models import SnorkelLocation

    return SnorkelLocation.objects.all()


def _run_once() -> None:
    import random

    from .snorkel import fetch_forecast
    from .history import save_forecast_history

    # Throttle between locations so a synchronized cache-expiry can never burst
    # the Open-Meteo rate limit. At the default 0.5s delay, even a full refresh of
    # ~1,000 locations stays around ~4 requests/sec (2 API calls each), well under
    # Open-Meteo's free-tier limits. Tune via SCHEDULER_REQUEST_DELAY_SECONDS.
    delay = float(os.getenv("SCHEDULER_REQUEST_DELAY_SECONDS", "0.5"))

    locations = _iter_locations()
    for location in locations:
        coords = location.coordinates_dict
        tz = location.timezone
        try:
            hours = fetch_forecast(
                coordinates=coords,
                timezone_str=tz,
                country_slug=location.country_slug,
                city_slug=location.city_slug,
            )
            save_forecast_history(location, None, hours)
        except Exception as e:  # noqa: BLE001
            print(
                f"[scheduler] Error for {location.country_slug}/{location.city_slug}: {e}",
                file=sys.stderr,
            )
        if delay > 0:
            # Small jitter avoids a regular request cadence.
            time.sleep(delay + random.uniform(0, delay))


def main() -> None:
    _setup_django()

    interval = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "1800"))
    enabled = str(os.getenv("ENABLE_SCHEDULER", "true")).lower() in {"1", "true", "yes", "on"}
    if not enabled:
        print("[scheduler] Disabled via ENABLE_SCHEDULER=false")
        return

    print(f"[scheduler] Starting with interval={interval}s")

    running = True

    def _stop(signum, frame):  # noqa: ANN001, D401
        nonlocal running
        print(f"[scheduler] Received signal {signum}, stopping...")
        running = False

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    # Initial run at start
    _run_once()

    while running:
        time.sleep(interval)
        _run_once()


if __name__ == "__main__":
    main()
