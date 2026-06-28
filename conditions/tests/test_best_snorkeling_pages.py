from datetime import timedelta

from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.utils import timezone

from conditions import views
from conditions.models import ForecastHour, SnorkelLocation


class BestSnorkelingPageTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.factory = RequestFactory()
        self.greece = SnorkelLocation.objects.create(
            osm_id=9001,
            osm_type="node",
            country_slug="greece",
            city_slug="milos",
            name="Milos",
            country="Greece",
            latitude=36.7,
            longitude=24.4,
            timezone="Europe/Athens",
            description="Clear coves and volcanic coast.",
            is_popular=True,
        )
        self.mexico = SnorkelLocation.objects.create(
            osm_id=9002,
            osm_type="node",
            country_slug="mexico",
            city_slug="cozumel",
            name="Cozumel",
            country="Mexico",
            latitude=20.4,
            longitude=-86.9,
            timezone="America/Cancun",
            description="Reef snorkeling with warm water.",
            is_popular=True,
        )

        now = timezone.now()
        self._create_hours(self.greece, now, future_score=0.86, historical_score=0.74)
        self._create_hours(self.mexico, now, future_score=0.68, historical_score=0.82)

    def _create_hours(
        self,
        location: SnorkelLocation,
        now,
        *,
        future_score: float,
        historical_score: float,
    ) -> None:
        rows = []
        for offset in range(1, 13):
            rows.append(
                ForecastHour(
                    location=location,
                    country_slug=location.country_slug,
                    city_slug=location.city_slug,
                    time=now + timedelta(hours=offset),
                    ok=future_score >= 0.6,
                    score=future_score,
                    rating="excellent" if future_score >= 0.8 else "good",
                    wave_height=0.18,
                    wind_speed=3.2,
                    sea_surface_temperature=25.4,
                )
            )
        for offset in range(1, 31):
            rows.append(
                ForecastHour(
                    location=location,
                    country_slug=location.country_slug,
                    city_slug=location.city_slug,
                    time=now - timedelta(hours=offset),
                    ok=historical_score >= 0.6,
                    score=historical_score,
                    rating="good",
                    wave_height=0.24,
                    wind_speed=3.8,
                    sea_surface_temperature=24.9,
                )
            )
        ForecastHour.objects.bulk_create(rows)

    def test_global_best_snorkeling_page_uses_stored_rankings(self):
        request = self.factory.get("/best-snorkeling/")
        response = views.best_snorkeling(request)

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()

        self.assertIn("Best places to snorkel in the world", html)
        self.assertIn("Top 10 best places to snorkel over the next 72 hours", html)
        self.assertIn("Milos", html)
        self.assertIn("Cozumel", html)
        self.assertIn("Best snorkeling in Greece", html)

    def test_country_page_renders_country_specific_ranking(self):
        request = self.factory.get("/greece/")
        response = views.country_directory(request, country="greece")

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()

        self.assertIn("Best snorkeling in Greece", html)
        self.assertIn("Best Greece spots over the next 72 hours", html)
        self.assertIn("Milos", html)
        self.assertNotIn("Cozumel</h3>", html)

    def test_country_rankings_skip_global_country_list_and_cap_history(self):
        rankings = views.get_best_snorkeling_rankings(
            "greece",
            include_countries=False,
            historical_limit=1,
        )

        self.assertEqual(rankings["countries"], [])
        self.assertEqual(len(rankings["historical"]), 1)
        self.assertEqual(rankings["historical"][0]["country_slug"], "greece")
