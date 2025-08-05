# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md

## Project Overview

SnorkelForecast.com is a Django 5.0 web application that provides snorkeling forecasts for Carboneras, Spain by integrating with Open-Meteo's free Marine & Weather APIs. The app displays a 72-hour forecast showing ideal snorkeling conditions based on wave height, wind speed, and sea temperature thresholds.

## Essential Commands

### Development Setup
```bash
# Install dependencies
uv venv                # Create virtual environment  
uv sync               # Install dependencies from uv.lock

# Run development server (from snorkelforecast/ directory)
cd snorkelforecast && python manage.py runserver

# Build CSS in watch mode 
npm run tailwind:watch

# Build CSS for production
npm run tailwind:build

# Lint code
uv run ruff check .
```

### Django Management 
```bash
# Run from snorkelforecast/ directory
python manage.py runserver        # Start dev server
python manage.py collectstatic    # Collect static files
python manage.py migrate          # Run migrations (if any added)
```

### Production Build
```bash
# Build CSS and collect static files
npm run tailwind:build
cd snorkelforecast && python manage.py collectstatic --noinput

# Run with gunicorn
PYTHONPATH=/app uv run gunicorn snorkelforecast.wsgi:application
```

## Architecture

### Project Structure
```
├── snorkelforecast/          # Django project directory
│   ├── snorkelforecast/      # Main Django config
│   │   ├── settings.py       # Django settings
│   │   ├── urls.py           # Main URL routing
│   │   └── wsgi.py           # WSGI config
│   └── manage.py             # Django management script
├── conditions/               # Main Django app
│   ├── snorkel.py           # Core business logic
│   ├── views.py             # Django views
│   ├── urls.py              # App URL routing
│   └── templates/           # Django templates
└── static/                  # Static files
    ├── src/input.css        # Tailwind source
    └── css/output.css       # Compiled CSS
```

### Core Components

1. **Business Logic (`conditions/snorkel.py`)**:
   - `fetch_forecast()`: Fetches weather data from Open-Meteo APIs
   - `CARBONERAS`: Hardcoded coordinates (lat: 36.997, lon: -1.896) 
   - `THRESHOLDS`: Snorkeling condition thresholds (wave height ≤ 0.3m, wind ≤ 4.5 m/s, water temp 22-29°C)
   - Returns list of `Hour` objects with `time` and `ok` (boolean) fields

2. **Views (`conditions/views.py`)**:
   - `home()`: Main view that fetches forecast data and renders template

3. **Template (`conditions/templates/conditions/index.html`)**:
   - Displays 72-hour grid with green (good) or gray (poor) conditions
   - Uses Tailwind CSS classes for styling
   - Responsive grid layout (6 cols mobile, 12 cols desktop)

### Key Dependencies

- **Django 5.0+**: Web framework
- **httpx**: HTTP client for API calls
- **python-dateutil**: Timezone handling  
- **whitenoise**: Static file serving in production
- **gunicorn**: WSGI server for production
- **Tailwind CSS**: Styling framework

## Development Notes

### API Integration
The app makes concurrent requests to two Open-Meteo endpoints:
- Marine API: Wave height, sea surface temperature
- Weather API: Wind speed at 10m

All data is fetched in UTC and converted to Europe/Madrid timezone for display.

### Static Files
- Input CSS: `static/src/input.css` (Tailwind directives)
- Output CSS: `static/css/output.css` (compiled, git-ignored)
- Use `npm run tailwind:watch` during development
- Django static files collected to `staticfiles/` for production

### Testing
The Django project currently has no explicit test setup. When adding tests:
- Use Django's built-in testing framework
- Mock API calls to Open-Meteo in tests
- Test threshold logic in `snorkel.py`

### Deployment 
Configured for containerized deployment (fly.io, Railway) with:
- Dockerfile using Python 3.13 slim
- WhiteNoise middleware for static file serving
- No database requirements (SQLite for Django admin only)

### Future Extensibility
Current MVP is Carboneras-only but designed for expansion:
- Coordinates are parameterized in `CARBONERAS` constant
- Template and view structure supports dynamic location data
- API calls can accept lat/lon parameters

## Development Tips
- Use `uv run` to execute Python commands in the virtual environment