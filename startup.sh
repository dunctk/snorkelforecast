#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Add project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Set Django settings module
export DJANGO_SETTINGS_MODULE=snorkelforecast.snorkelforecast.settings

# Run Django migrations
uv run python snorkelforecast/manage.py migrate

# Populate database with popular locations (only if empty)
echo "Checking database population..."
LOCATION_COUNT=$(uv run python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'snorkelforecast.snorkelforecast.settings')
django.setup()
from conditions.models import SnorkelLocation
print(SnorkelLocation.objects.count())
")

if [ "$LOCATION_COUNT" -eq 0 ]; then
    echo "Database is empty, populating with popular locations..."
    uv run python snorkelforecast/manage.py migrate_popular_locations
else
    echo "Database already has $LOCATION_COUNT locations, skipping population."
fi

# Collect static files
uv run python snorkelforecast/manage.py collectstatic --noinput

# Start background scheduler (optional)
if [ -z "$ENABLE_SCHEDULER" ] || [[ "$ENABLE_SCHEDULER" =~ ^([Tt]rue|[Yy]es|1|on)$ ]]; then
  echo "Starting in-process scheduler..."
  uv run python -m conditions.scheduler &
fi

# Start Gunicorn server
gunicorn snorkelforecast.snorkelforecast.wsgi:application --bind 0.0.0.0:8000
