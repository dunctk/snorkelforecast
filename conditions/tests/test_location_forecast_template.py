import json
import re
from datetime import datetime, timedelta
from unittest.mock import patch

from dateutil import tz
from django.test import RequestFactory, TestCase

from conditions import views
from conditions.models import ForecastHour, SnorkelLocation


def _build_hour(
    start_time: datetime,
    hour: int,
    *,
    ok: bool = True,
    rating: str = "good",
) -> dict:
    return {
        "time": start_time + timedelta(hours=hour),
        "ok": ok,
        "score": 0.8 if ok else 0.3,
        "rating": rating,
        "wave_ok": ok,
        "wind_ok": ok,
        "sst_ok": ok,
        "slack_ok": True,
        "light_ok": True,
        "wave_height": 0.2,
        "wind_speed": 4.1,
        "sea_surface_temperature": 24.4,
        "sea_level_height": 0.9,
        "is_high_tide": False,
    }


class LocationForecastTemplateTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.location_main = SnorkelLocation.objects.create(
            osm_id=2020,
            osm_type="node",
            country_slug="spain",
            city_slug="primary-spot",
            name="Primary Spot",
            country="Spain",
            latitude=36.997,
            longitude=-1.896,
            timezone="Europe/Madrid",
        )
        self.location_nearby = SnorkelLocation.objects.create(
            osm_id=2021,
            osm_type="node",
            country_slug="spain",
            city_slug="nearby-spot",
            name="Nearby Spot",
            country="Spain",
            latitude=36.998,
            longitude=-1.897,
            timezone="Europe/Madrid",
        )

    def _forecast_payload(self, *, include_ok: bool = True) -> dict:
        now = datetime.now(tz=tz.gettz("Europe/Madrid")) + timedelta(hours=1)
        if include_ok:
            rating = "excellent"
            first_hour_ok = True
        else:
            rating = "poor"
            first_hour_ok = False

        hours = [
            _build_hour(now, i, ok=first_hour_ok and i < 3, rating=rating)
            for i in range(12)
        ]
        return {
            "hours": hours,
            "source": "snapshot",
            "generated_at": now,
            "next_refresh_at": now + timedelta(minutes=20),
            "is_stale": False,
        }

    @patch("conditions.views.fetch_forecast_payload")
    def test_location_forecast_renders_decision_sections_and_collapsibles(self, mock_payload):
        mock_payload.side_effect = [self._forecast_payload(), self._forecast_payload()]

        request = self.factory.get(
            f"/{self.location_main.country_slug}/{self.location_main.city_slug}/"
        )
        response = views.location_forecast(
            request,
            country=self.location_main.country_slug,
            city=self.location_main.city_slug,
        )

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()

        self.assertIn('id="forecast-verdict"', html)
        self.assertIn('id="day-planner"', html)
        self.assertIn('id="best-available"', html)
        self.assertIn('id="advanced-data"', html)

        # Decision-first ordering: forecast verdict -> 3-day planner -> best available -> advanced.
        self.assertLess(html.index('id="forecast-verdict"'), html.index('id="day-planner"'))
        self.assertLess(html.index('id="day-planner"'), html.index('id="best-available"'))
        self.assertLess(html.index('id="best-available"'), html.index('id="advanced-data"'))

        for action in ["#day-planner", "#best-available", "#advanced-data"]:
            self.assertIn(f'href="{action}"', html)

        self.assertGreaterEqual(html.count("<details"), 3)
        self.assertIn("72-hour forecast overview", html)
        self.assertIn("Scoring methodology (for technical users)", html)
        self.assertIn("Detailed hourly data table", html)

    @patch("conditions.views.fetch_forecast_payload")
    def test_location_forecast_mobile_action_buttons_have_touch_targets(self, mock_payload):
        mock_payload.side_effect = [self._forecast_payload(), self._forecast_payload()]

        request = self.factory.get(
            f"/{self.location_main.country_slug}/{self.location_main.city_slug}/"
        )
        response = views.location_forecast(
            request,
            country=self.location_main.country_slug,
            city=self.location_main.city_slug,
        )

        html = response.content.decode()

        for action in ["#day-planner", "#best-available", "#advanced-data"]:
            match = re.search(rf'<a[^>]+href="{re.escape(action)}"[^>]*>', html)
            self.assertIsNotNone(match)
            self.assertIn("touch-target", match.group(0))

        self.assertNotIn("Skip to forecast", html)
        self.assertNotIn("Skip to hourly table", html)

    @patch("conditions.views.fetch_forecast_payload")
    def test_location_forecast_jsonld_schema_stays_intact(self, mock_payload):
        mock_payload.side_effect = [self._forecast_payload(), self._forecast_payload()]

        request = self.factory.get(
            f"/{self.location_main.country_slug}/{self.location_main.city_slug}/"
        )
        response = views.location_forecast(
            request,
            country=self.location_main.country_slug,
            city=self.location_main.city_slug,
        )

        html = response.content.decode()
        schema_blocks = re.findall(
            r'<script type="application/ld\+json">\s*(\[.*?\])\s*</script>',
            html,
            flags=re.S,
        )
        self.assertGreaterEqual(len(schema_blocks), 1)

        schema = json.loads(schema_blocks[0])
        self.assertIsInstance(schema, list)
        types = {entry.get("@type") for entry in schema}
        self.assertEqual(types, {"TouristDestination", "BreadcrumbList", "FAQPage"})

        faq = next(entry for entry in schema if entry.get("@type") == "FAQPage")
        self.assertEqual(len(faq.get("mainEntity", [])), 3)
        self.assertEqual(faq["mainEntity"][0].get("@type"), "Question")
        self.assertIn("acceptedAnswer", faq["mainEntity"][0])

    @patch("conditions.views.fetch_forecast_payload")
    def test_location_forecast_can_shift_advanced_charts_to_yesterday(self, mock_payload):
        mock_payload.return_value = self._forecast_payload()
        local_tz = tz.gettz("Europe/Madrid")
        start = datetime.now(tz=local_tz).replace(minute=0, second=0, microsecond=0) - timedelta(days=1)
        ForecastHour.objects.create(
            location=self.location_main,
            country_slug=self.location_main.country_slug,
            city_slug=self.location_main.city_slug,
            time=start,
            ok=True,
            score=0.91,
            rating="excellent",
            wave_height=0.1,
            wind_speed=2.0,
            sea_surface_temperature=24.0,
            sea_level_height=0.4,
            current_velocity=0.1,
        )

        request = self.factory.get(
            f"/{self.location_main.country_slug}/{self.location_main.city_slug}/?history_days=1"
        )
        response = views.location_forecast(
            request,
            country=self.location_main.country_slug,
            city=self.location_main.city_slug,
        )

        html = response.content.decode()

        self.assertIn("Viewing historical data", html)
        self.assertIn("?history_days=0#advanced-data", html)
        self.assertIn("72-hour historical overview", html)
        self.assertIn(start.strftime("%a %H:00"), html)
        self.assertIn("0.91", html)
