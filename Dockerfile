FROM python:3.13-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED 1

COPY pyproject.toml uv.lock /app/
RUN pip install uv && uv sync

COPY snorkelforecast/manage.py /app/

# Run collectstatic
RUN uv run python manage.py collectstatic --noinput

# Set the command to run the application
CMD uv run gunicorn snorkelforecast.wsgi:application