from __future__ import annotations

from django.utils import translation


def _english_path(path: str) -> str:
    if path == "/es":
        return "/"
    if path.startswith("/es/"):
        stripped = path[3:]
        return stripped if stripped.startswith("/") else f"/{stripped}"
    return path


def _spanish_path(path: str) -> str:
    base = _english_path(path)
    if base == "/":
        return "/es/"
    return f"/es{base}"


UI_TEXT = {
    "en": {
        "site_name": "SnorkelForecast.com",
        "nav_countries": "Countries",
        "nav_best": "Best snorkeling",
        "nav_search": "Search",
        "nav_guides": "Guides",
        "nav_popular": "Popular",
        "nav_how": "How it works",
        "nav_open_meteo": "Open-Meteo",
        "footer_popular": "Popular spots",
        "footer_more": "More destinations",
        "footer_guides": "Guides",
        "footer_explore": "Explore",
        "footer_best_time": "Best time to snorkel",
        "footer_water_temp": "Water temperature",
        "footer_all_guides": "All guides",
        "footer_all_countries": "All countries",
        "footer_search_spots": "Search spots",
        "footer_home": "Home",
        "footer_powered": "Powered by Open-Meteo - Forecasts update hourly",
        "footer_made_by": "Made by",
        "footer_open_source": "This site is",
        "footer_open_source_link": "open source",
        "footer_star": "Star on GitHub",
        "language": "Language",
        "english": "English",
        "spanish": "Español",
    },
    "es": {
        "site_name": "SnorkelForecast.com",
        "nav_countries": "Países",
        "nav_best": "Mejor snorkel",
        "nav_search": "Buscar",
        "nav_guides": "Guías",
        "nav_popular": "Populares",
        "nav_how": "Cómo funciona",
        "nav_open_meteo": "Open-Meteo",
        "footer_popular": "Lugares populares",
        "footer_more": "Más destinos",
        "footer_guides": "Guías",
        "footer_explore": "Explorar",
        "footer_best_time": "Mejor hora para hacer snorkel",
        "footer_water_temp": "Temperatura del agua",
        "footer_all_guides": "Todas las guías",
        "footer_all_countries": "Todos los países",
        "footer_search_spots": "Buscar lugares",
        "footer_home": "Inicio",
        "footer_powered": "Con datos de Open-Meteo - Pronósticos actualizados cada hora",
        "footer_made_by": "Hecho por",
        "footer_open_source": "Este sitio es",
        "footer_open_source_link": "open source",
        "footer_star": "Ver en GitHub",
        "language": "Idioma",
        "english": "English",
        "spanish": "Español",
    },
}


def language_context(request):
    language_code = translation.get_language() or "en"
    language = "es" if language_code.startswith("es") else "en"
    path = request.path
    english_path = _english_path(path)
    spanish_path = _spanish_path(path)
    return {
        "active_language": language,
        "is_spanish": language == "es",
        "html_language": "es" if language == "es" else "en",
        "ui": UI_TEXT[language],
        "localized_prefix": "/es" if language == "es" else "",
        "english_path": english_path,
        "spanish_path": spanish_path,
        "absolute_english_url": request.build_absolute_uri(english_path),
        "absolute_spanish_url": request.build_absolute_uri(spanish_path),
    }
