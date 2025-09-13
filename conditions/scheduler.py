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
    from .snorkel import fetch_forecast
    from .history import save_forecast_history

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
