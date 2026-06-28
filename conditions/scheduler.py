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

    from .snorkel import fetch_forecast_payload
    from .history import save_forecast_history

    # Throttle between locations so a synchronized cache-expiry can never burst
    # the Open-Meteo rate limit. At the default 0.5s delay, even a full refresh of
    # ~1,000 locations stays around ~4 requests/sec (2 API calls each), well under
    # Open-Meteo's free-tier limits. Tune via SCHEDULER_REQUEST_DELAY_SECONDS.
    delay = float(os.getenv("SCHEDULER_REQUEST_DELAY_SECONDS", "0.5"))

    locations = _iter_locations()
    refreshed_country_slugs: set[str] = set()
    for location in locations:
        coords = location.coordinates_dict
        tz = location.timezone
        refreshed_country_slugs.add(location.country_slug)
        try:
            payload = fetch_forecast_payload(
                coordinates=coords,
                timezone_str=tz,
                country_slug=location.country_slug,
                city_slug=location.city_slug,
                location=location,
            )
            hours = payload.get("hours", [])
            source = payload.get("source", "unknown")
            stale = payload.get("is_stale", False)
            print(
                f"[scheduler] {location.country_slug}/{location.city_slug}: "
                f"source={source} hours={len(hours)} stale={stale}"
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

    try:
        from .views import warm_best_snorkeling_ranking_cache

        warm_best_snorkeling_ranking_cache(sorted(refreshed_country_slugs))
        print(
            f"[scheduler] warmed ranking caches for {len(refreshed_country_slugs)} countries"
        )
    except Exception as e:  # noqa: BLE001
        print(f"[scheduler] ranking cache warm failed: {e}", file=sys.stderr)

    try:
        from django.conf import settings

        if getattr(settings, "ALERT_EMAILS_ENABLED", False):
            from .alerts import send_due_alerts

            result = send_due_alerts()
            print(
                "[scheduler] alerts checked={checked} matched={matched} sent={sent}".format(
                    **result
                )
            )
    except Exception as e:  # noqa: BLE001
        print(f"[scheduler] alert send failed: {e}", file=sys.stderr)


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
