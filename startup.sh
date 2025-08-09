#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Add project root to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Set Django settings module
export DJANGO_SETTINGS_MODULE=snorkelforecast.snorkelforecast.settings

# Run Django migrations
uv run python snorkelforecast/manage.py migrate

# Collect static files
uv run python snorkelforecast/manage.py collectstatic --noinput

# Start background scheduler (optional)
if [ -z "$ENABLE_SCHEDULER" ] || [[ "$ENABLE_SCHEDULER" =~ ^([Tt]rue|[Yy]es|1|on)$ ]]; then
  echo "Starting in-process scheduler..."
  uv run python -m conditions.scheduler &
fi

# Start Gunicorn server
gunicorn snorkelforecast.snorkelforecast.wsgi:application --bind 0.0.0.0:8000
