from datetime import datetime, timedelta
from unittest.mock import patch

from dateutil import tz
from django.core.cache import cache
from django.test import Client, TestCase
from django.utils import translation

from conditions.models import SnorkelLocation


def _forecast_payload() -> dict:
    start_time = datetime.now(tz=tz.gettz("Europe/Madrid")) + timedelta(hours=1)
    hours = []
    for hour in range(12):
        hours.append(
            {
                "time": start_time + timedelta(hours=hour),
                "ok": True,
                "score": 0.82,
                "rating": "excellent",
                "wave_ok": True,
                "wind_ok": True,
                "sst_ok": True,
                "slack_ok": True,
                "light_ok": True,
                "wave_height": 0.2,
                "wind_speed": 3.1,
                "sea_surface_temperature": 24.2,
                "sea_level_height": 0.8,
                "current_velocity": 0.05,
                "is_high_tide": False,
            }
        )
    return {
        "hours": hours,
        "source": "snapshot",
        "generated_at": start_time,
        "next_refresh_at": start_time + timedelta(minutes=30),
        "is_stale": False,
    }


class I18nSeoTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        translation.activate("en")
        self.client = Client(HTTP_HOST="snorkelforecast.com")

    def tearDown(self) -> None:
        translation.activate("en")

    def test_default_homepage_stays_english_unprefixed(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('<html lang="en">', html)
        self.assertIn('hreflang="en" href="https://snorkelforecast.com/"', html)
        self.assertIn('hreflang="es" href="https://snorkelforecast.com/es/"', html)
        self.assertIn("Know exactly when", html)

    def test_spanish_homepage_uses_es_prefix_and_hreflang(self):
        response = self.client.get("/es/")

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('<html lang="es">', html)
        self.assertIn('hreflang="en" href="https://snorkelforecast.com/"', html)
        self.assertIn('hreflang="es" href="https://snorkelforecast.com/es/"', html)
        self.assertIn("Pronósticos de snorkel", html)
        self.assertIn('href="/es/search/"', html)

    def test_spanish_best_snorkeling_page_has_spanish_metadata(self):
        response = self.client.get("/es/best-snorkeling/")

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Mejores lugares para hacer snorkel", html)
        self.assertIn(
            'hreflang="en" href="https://snorkelforecast.com/best-snorkeling/"',
            html,
        )
        self.assertIn(
            'hreflang="es" href="https://snorkelforecast.com/es/best-snorkeling/"',
            html,
        )

    @patch("conditions.views.fetch_forecast_payload")
    def test_spanish_location_forecast_uses_localized_url_and_copy(self, mock_payload):
        mock_payload.return_value = _forecast_payload()
        SnorkelLocation.objects.create(
            osm_id=5101,
            osm_type="node",
            country_slug="spain",
            city_slug="carboneras",
            name="Carboneras",
            country="Spain",
            latitude=36.996,
            longitude=-1.896,
            timezone="Europe/Madrid",
        )

        response = self.client.get("/es/spain/carboneras/")

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('<html lang="es">', html)
        self.assertIn("Pronóstico de snorkel en Carboneras hoy", html)
        self.assertIn(
            'hreflang="en" href="https://snorkelforecast.com/spain/carboneras/"',
            html,
        )
        self.assertIn(
            'hreflang="es" href="https://snorkelforecast.com/es/spain/carboneras/"',
            html,
        )
        self.assertIn('"url": "https://snorkelforecast.com/es/spain/carboneras/"', html)

    def test_sitemap_exposes_spanish_urls_and_alternates(self):
        SnorkelLocation.objects.create(
            osm_id=5102,
            osm_type="node",
            country_slug="spain",
            city_slug="carboneras",
            name="Carboneras",
            country="Spain",
            latitude=36.996,
            longitude=-1.896,
            timezone="Europe/Madrid",
        )

        response = self.client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        xml = response.content.decode()
        self.assertNotIn("https://snorkelforecast.com/en/", xml)
        self.assertIn("https://snorkelforecast.com/es/best-snorkeling/", xml)
        self.assertIn("https://snorkelforecast.com/es/spain/carboneras/", xml)
        self.assertIn("https://snorkelforecast.com/es/spain/carboneras/sea-temperature/", xml)
        self.assertIn('hreflang="es"', xml)
        self.assertIn('hreflang="x-default"', xml)

    def test_spanish_guides_use_translated_article_content(self):
        response = self.client.get("/es/guides/best-time-to-snorkel/")

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Mejor hora para hacer snorkel", html)
        self.assertIn("Marea: busca la ventana alrededor de la pleamar", html)
        self.assertIn("Preguntas frecuentes", html)
        self.assertNotIn("Ask any experienced snorkeler", html)

    def test_spanish_static_directory_and_history_pages_render(self):
        SnorkelLocation.objects.create(
            osm_id=5104,
            osm_type="node",
            country_slug="spain",
            city_slug="carboneras",
            name="Carboneras",
            country="Spain",
            latitude=36.996,
            longitude=-1.896,
            timezone="Europe/Madrid",
            is_popular=True,
        )

        pages = {
            "/es/countries/": "Destinos de snorkel por país",
            "/es/search/": "Buscar lugares para hacer snorkel",
            "/es/guides/": "Guías de snorkel",
            "/es/spain/": "Mejor snorkel en Spain",
            "/es/spain/carboneras/history/": "Tendencias históricas",
            "/es/spain/carboneras/embed/sea-temperature/": '<html lang="es">',
        }

        for path, expected in pages.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                self.assertIn(expected, html)

    @patch("conditions.views.fetch_forecast_payload")
    def test_spanish_sea_temperature_page_uses_localized_copy_and_valid_chart_data(
        self, mock_payload
    ):
        mock_payload.return_value = _forecast_payload()
        SnorkelLocation.objects.create(
            osm_id=5103,
            osm_type="node",
            country_slug="spain",
            city_slug="carboneras",
            name="Carboneras",
            country="Spain",
            latitude=36.996,
            longitude=-1.896,
            timezone="Europe/Madrid",
        )

        response = self.client.get("/es/spain/carboneras/sea-temperature/")

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Temperatura del mar en Carboneras", html)
        self.assertIn("¿Se puede nadar en Carboneras hoy?", html)
        self.assertIn(
            'hreflang="en" href="https://snorkelforecast.com/spain/carboneras/sea-temperature/"',
            html,
        )
        self.assertIn(
            'hreflang="es" href="https://snorkelforecast.com/es/spain/carboneras/sea-temperature/"',
            html,
        )
        self.assertNotIn("const sstAvgData = [24,2", html)
