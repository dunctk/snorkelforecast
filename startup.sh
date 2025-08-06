#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Run Django migrations
python snorkelforecast/manage.py migrate

# Collect static files
python snorkelforecast/manage.py collectstatic --noinput

# Start Gunicorn server
gunicorn snorkelforecast.snorkelforecast.wsgi:application --bind 0.0.0.0:8000
