FROM python:3.13-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED 1

COPY pyproject.toml uv.lock /app/
RUN pip install uv && uv sync

COPY . /app

RUN PYTHONPATH=/app uv run python manage.py collectstatic --noinput

CMD PYTHONPATH=/app uv run gunicorn snorkelforecast.wsgi:application