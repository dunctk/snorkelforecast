from __future__ import annotations

from django.utils import translation


EN_TO_ES_SEGMENTS = {
    "best-snorkeling": "mejor-snorkel",
    "countries": "destinos",
    "search": "buscar",
    "guides": "guias",
    "sea-temperature": "temperatura-del-mar",
    "alerts": "alertas",
    "history": "historial",
    "usa": "estados-unidos",
    "spain": "espana",
}
ES_TO_EN_SEGMENTS = {value: key for key, value in EN_TO_ES_SEGMENTS.items()}


def _translate_path_segments(path: str, mapping: dict[str, str]) -> str:
    suffix_slash = path.endswith("/")
    query = ""
    if "?" in path:
        path, query = path.split("?", 1)
        query = f"?{query}"
    segments = [segment for segment in path.strip("/").split("/") if segment]
    translated = [mapping.get(segment, segment) for segment in segments]
    translated_path = "/" + "/".join(translated)
    if suffix_slash and translated_path != "/":
        translated_path += "/"
    return f"{translated_path}{query}"


def _english_path(path: str) -> str:
    if path == "/es":
        return "/"
    if path.startswith("/es/"):
        stripped = path[3:]
        base = stripped if stripped.startswith("/") else f"/{stripped}"
        return _translate_path_segments(base, ES_TO_EN_SEGMENTS)
    return _translate_path_segments(path, ES_TO_EN_SEGMENTS)


def _spanish_path(path: str) -> str:
    base = _english_path(path)
    base = _translate_path_segments(base, EN_TO_ES_SEGMENTS)
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
