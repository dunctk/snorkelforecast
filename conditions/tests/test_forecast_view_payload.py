from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.utils import timezone
from django.core.cache import cache

from conditions.models import SnorkelLocation
from conditions.snorkel import _save_forecast_snapshot
from conditions import views


class ForecastPayloadViewTests(TestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.location_main = SnorkelLocation.objects.create(
            osm_id=1010,
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
            osm_id=1011,
            osm_type="node",
            country_slug="spain",
            city_slug="nearby-spot",
            name="Nearby Spot",
            country="Spain",
            latitude=36.998,
            longitude=-1.897,
            timezone="Europe/Madrid",
        )

    @patch("conditions.views.fetch_forecast_payload")
    def test_location_forecast_does_not_allow_api_calls(self, mock_payload):
        cache.clear()
        mock_payload.return_value = {
            "hours": [],
            "source": "snapshot",
            "generated_at": timezone.now(),
            "next_refresh_at": None,
            "is_stale": True,
        }

        request = self.factory.get(
            f"/{self.location_main.country_slug}/{self.location_main.city_slug}/"
        )
        response = views.location_forecast(
            request,
            country=self.location_main.country_slug,
            city=self.location_main.city_slug,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_payload.call_count, 2)
        main_call, nearby_call = mock_payload.call_args_list
        self.assertFalse(main_call.kwargs["allow_api"])
        self.assertFalse(nearby_call.kwargs["allow_api"])
        self.assertEqual(main_call.kwargs["location"].pk, self.location_main.pk)
        self.assertEqual(nearby_call.kwargs["location"].pk, self.location_nearby.pk)
        self.assertIn("Source: Snapshot", response.content.decode())

    @patch("conditions.views.fetch_forecast_payload")
    def test_sea_temperature_views_do_not_allow_api_calls(self, mock_payload):
        cache.clear()
        mock_payload.return_value = {
            "hours": [],
            "source": "snapshot",
            "generated_at": timezone.now(),
            "next_refresh_at": None,
            "is_stale": True,
        }

        request = self.factory.get(
            f"/{self.location_main.country_slug}/{self.location_main.city_slug}/sea-temperature/"
        )
        response = views.location_sea_temperature(
            request,
            country=self.location_main.country_slug,
            city=self.location_main.city_slug,
        )
        self.assertEqual(response.status_code, 200)

        request = self.factory.get(
            f"/{self.location_main.country_slug}/{self.location_main.city_slug}/embed/sea-temperature/"
        )
        embed_response = views.location_sea_temperature_embed(
            request,
            country=self.location_main.country_slug,
            city=self.location_main.city_slug,
        )
        self.assertEqual(embed_response.status_code, 200)

        self.assertEqual(mock_payload.call_count, 2)
        self.assertFalse(mock_payload.call_args_list[0].kwargs["allow_api"])
        self.assertFalse(mock_payload.call_args_list[1].kwargs["allow_api"])


class SnorkelSnapshotPersistenceTests(TestCase):
    @patch("conditions.snorkel.LocationForecastSnapshot.objects.update_or_create")
    def test_save_forecast_snapshot_uses_requested_horizon(self, mock_update):
        _save_forecast_snapshot(
            snapshot_key="forecast-snapshot:test",
            coordinates={"lat": 36.997, "lon": -1.896},
            timezone_str="UTC",
            country_slug="spain",
            city_slug="carboneras",
            location=None,
            hours=24,
            payload=[],
        )

        self.assertEqual(mock_update.call_count, 1)
        _, kwargs = mock_update.call_args
        self.assertEqual(kwargs["defaults"]["horizon_hours"], 24)
        self.assertEqual(kwargs["defaults"]["timezone"], "UTC")
