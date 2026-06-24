from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from conditions.models import SnorkelLocation


class SchedulerTests(TestCase):
    def setUp(self) -> None:
        self.location = SnorkelLocation.objects.create(
            osm_id=3030,
            osm_type="node",
            country_slug="spain",
            city_slug="carboneras",
            name="Carboneras",
            country="Spain",
            latitude=36.997,
            longitude=-1.896,
            timezone="Europe/Madrid",
        )

    def test_scheduler_calls_payload_fetch_and_persists_history(self):
        now = timezone.now()
        payload = {
            "hours": [
                {
                    "time": now,
                    "ok": True,
                    "score": 0.77,
                    "rating": "good",
                    "wave_ok": True,
                    "wind_ok": True,
                    "sst_ok": True,
                    "slack_ok": True,
                    "light_ok": True,
                    "wave_height": 0.25,
                    "wind_speed": 3.5,
                    "sea_surface_temperature": 24.1,
                    "sea_level_height": 1.0,
                    "is_high_tide": False,
                }
            ],
            "source": "api",
            "generated_at": now,
            "next_refresh_at": now,
            "is_stale": False,
        }

        with (
            patch.dict("conditions.scheduler.os.environ", {"SCHEDULER_REQUEST_DELAY_SECONDS": "0"}),
            patch("conditions.scheduler._iter_locations", return_value=[self.location]) as mock_iter,
            patch("conditions.scheduler.time.sleep") as mock_sleep,
            patch("conditions.snorkel.fetch_forecast_payload", return_value=payload) as mock_payload,
            patch("conditions.history.save_forecast_history") as mock_save_history,
        ):

            from conditions.scheduler import _run_once

            _run_once()

            mock_iter.assert_called_once_with()
            mock_payload.assert_called_once_with(
                coordinates=self.location.coordinates_dict,
                timezone_str=self.location.timezone,
                country_slug=self.location.country_slug,
                city_slug=self.location.city_slug,
                location=self.location,
            )
            mock_save_history.assert_called_once_with(self.location, None, payload["hours"])
            mock_sleep.assert_not_called()
