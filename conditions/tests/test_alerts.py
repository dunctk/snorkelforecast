from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from conditions.alerts import rating_reaches, send_due_alerts
from conditions.models import AlertSubscription, ForecastHour, SnorkelLocation


class AlertTests(TestCase):
    def setUp(self) -> None:
        self.location = SnorkelLocation.objects.create(
            osm_id=7070,
            osm_type="manual",
            country_slug="usa",
            city_slug="test-bay",
            name="Test Bay",
            country="USA",
            latitude=20.0,
            longitude=-156.0,
            timezone="Pacific/Honolulu",
            source="manual",
        )

    def test_rating_reaches_threshold(self):
        self.assertTrue(rating_reaches("excellent", "good"))
        self.assertTrue(rating_reaches("good", "good"))
        self.assertFalse(rating_reaches("fair", "good"))

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ALERT_EMAILS_ENABLED=True,
        SITE_BASE_URL="https://snorkelforecast.com",
    )
    def test_send_due_alerts_sends_matching_forecast(self):
        AlertSubscription.objects.create(
            email="person@example.com",
            location=self.location,
            min_rating="good",
        )
        ForecastHour.objects.create(
            location=self.location,
            country_slug=self.location.country_slug,
            city_slug=self.location.city_slug,
            time=timezone.now() + timedelta(hours=2),
            ok=True,
            score=0.83,
            rating="good",
            wave_height=0.3,
            wind_speed=2.5,
            sea_surface_temperature=26.4,
        )

        result = send_due_alerts()

        self.assertEqual(result["checked"], 1)
        self.assertEqual(result["matched"], 1)
        self.assertEqual(result["sent"], 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Test Bay snorkel alert", mail.outbox[0].subject)
        self.assertIn("/usa/test-bay/", mail.outbox[0].body)

    def test_subscribe_view_creates_subscription(self):
        response = self.client.post(
            reverse(
                "location_alert_subscribe",
                kwargs={"country": self.location.country_slug, "city": self.location.city_slug},
            ),
            {"email": "PERSON@example.com", "min_rating": "good"},
        )

        self.assertEqual(response.status_code, 200)
        subscription = AlertSubscription.objects.get(location=self.location)
        self.assertEqual(subscription.email, "person@example.com")
        self.assertTrue(subscription.is_active)

    def test_unsubscribe_view_disables_subscription(self):
        subscription = AlertSubscription.objects.create(
            email="person@example.com",
            location=self.location,
            min_rating="good",
        )

        response = self.client.get(reverse("alert_unsubscribe", kwargs={"token": subscription.token}))

        self.assertEqual(response.status_code, 200)
        subscription.refresh_from_db()
        self.assertFalse(subscription.is_active)
