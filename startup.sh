#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Add project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Set Django settings module
export DJANGO_SETTINGS_MODULE=snorkelforecast.snorkelforecast.settings

# Run Django migrations
uv run python snorkelforecast/manage.py migrate

# Populate database with locations (only if empty)
echo "Checking database population..."
LOCATION_COUNT=$(uv run python snorkelforecast/manage.py shell -c "
from conditions.models import SnorkelLocation
from conditions.models_spots import OSMSpot
legacy_count = SnorkelLocation.objects.count()
osm_count = OSMSpot.objects.count()
print(legacy_count + osm_count)
")

if [ "$LOCATION_COUNT" -eq 0 ]; then
    echo "Database is empty, populating with popular locations..."
    uv run python snorkelforecast/manage.py migrate_popular_locations
    uv run python snorkelforecast/manage.py populate_known_locations
else
    echo "Database already has $LOCATION_COUNT locations, skipping population."
fi

# Always ensure curated snorkeling spots exist (idempotent on every deploy).
# Non-fatal: a seeding hiccup must never abort boot under `set -e` and break the
# deploy — the app can start and serve while spots are (re)seeded on a later boot.
echo "Ensuring Hawaii snorkeling spots are present..."
uv run python snorkelforecast/manage.py populate_hawaii_spots || echo "populate_hawaii_spots failed (non-fatal)."
echo "Ensuring worldwide snorkeling spots are present..."
uv run python snorkelforecast/manage.py populate_world_spots || echo "populate_world_spots failed (non-fatal)."

# Optional: Run OSM import if enabled
if [ -n "$ENABLE_OSM_IMPORT" ] && [[ "$ENABLE_OSM_IMPORT" =~ ^([Tt]rue|[Yy]es|1|on)$ ]]; then
    echo "OSM import enabled, starting tile-based import..."
    # Create initial tile queue for coastal areas (can be customized)
    uv run python snorkelforecast/manage.py import_osm_tiles --create-tiles --zoom 8 --country-bbox "35,-10,45,5"
    # Run import for a few tiles
    uv run python snorkelforecast/manage.py import_osm_tiles --batch-size 5
fi

# Collect static files
uv run python snorkelforecast/manage.py collectstatic --noinput

# Notify search engines (Bing/Yandex/DuckDuckGo/etc.) of all URLs via IndexNow.
# Runs after the app is configured so the /<key>.txt verification file is live.
# Best-effort: never fail the boot if the network call errors.
echo "Submitting URLs to IndexNow..."
uv run python snorkelforecast/manage.py indexnow_submit || echo "IndexNow submission skipped/failed (non-fatal)."

# Start background scheduler (optional)
if [ -z "$ENABLE_SCHEDULER" ] || [[ "$ENABLE_SCHEDULER" =~ ^([Tt]rue|[Yy]es|1|on)$ ]]; then
  echo "Starting in-process scheduler..."
  uv run python -m conditions.scheduler &
fi

# Start Gunicorn server
gunicorn snorkelforecast.snorkelforecast.wsgi:application --bind 0.0.0.0:8000
