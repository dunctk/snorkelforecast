from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from django.utils import timezone

from .models import AlertSubscription, ForecastHour, SnorkelLocation


RATING_ORDER = {"poor": 0, "fair": 1, "good": 2, "excellent": 3}


@dataclass(frozen=True)
class AlertCandidate:
    subscription: AlertSubscription
    hour: ForecastHour


def rating_reaches(actual: str | None, minimum: str) -> bool:
    return RATING_ORDER.get(actual or "poor", 0) >= RATING_ORDER.get(minimum, 2)


def subscribe_to_location(
    *,
    email: str,
    location: SnorkelLocation,
    min_rating: str = "good",
) -> tuple[AlertSubscription, bool]:
    normalized_email = email.strip().lower()
    try:
        subscription, created = AlertSubscription.objects.update_or_create(
            email=normalized_email,
            location=location,
            defaults={"min_rating": min_rating, "is_active": True},
        )
    except IntegrityError:
        subscription = AlertSubscription.objects.get(
            email=normalized_email,
            location=location,
        )
        subscription.min_rating = min_rating
        subscription.is_active = True
        subscription.save(update_fields=["min_rating", "is_active", "updated_at"])
        created = False
    return subscription, created


def find_alert_candidate(subscription: AlertSubscription) -> AlertCandidate | None:
    now = timezone.now()
    cooldown_at = now - timedelta(hours=getattr(settings, "ALERT_EMAIL_COOLDOWN_HOURS", 18))
    if subscription.last_sent_at and subscription.last_sent_at >= cooldown_at:
        return None

    lookahead = now + timedelta(hours=getattr(settings, "ALERT_FORECAST_LOOKAHEAD_HOURS", 24))
    rows = (
        ForecastHour.objects.filter(
            location=subscription.location,
            time__gte=now,
            time__lte=lookahead,
        )
        .order_by("-ok", "-score", "time")
    )
    for hour in rows:
        if rating_reaches(hour.rating, subscription.min_rating):
            return AlertCandidate(subscription=subscription, hour=hour)
    return None


def build_alert_email(candidate: AlertCandidate) -> tuple[str, str]:
    subscription = candidate.subscription
    location = subscription.location
    hour = candidate.hour
    base_url = getattr(settings, "SITE_BASE_URL", "https://snorkelforecast.com").rstrip("/")
    location_url = f"{base_url}/{location.country_slug}/{location.city_slug}/"
    unsubscribe_url = f"{base_url}/alerts/unsubscribe/{subscription.token}/"
    score = round((hour.score or 0) * 10, 1)
    subject = f"{location.name} snorkel alert: {hour.rating.title()} around {hour.time:%a %H:%M}"
    body = (
        f"{location.name} is forecast to reach {hour.rating} snorkel conditions.\n\n"
        f"Best matching window: {hour.time:%A %H:%M}\n"
        f"Score: {score}/10\n"
        f"Wave height: {hour.wave_height if hour.wave_height is not None else 'n/a'} m\n"
        f"Wind: {hour.wind_speed if hour.wind_speed is not None else 'n/a'} m/s\n"
        f"Water temperature: "
        f"{hour.sea_surface_temperature if hour.sea_surface_temperature is not None else 'n/a'} C\n\n"
        f"Open the live report:\n{location_url}\n\n"
        f"Unsubscribe:\n{unsubscribe_url}\n"
    )
    return subject, body


def send_due_alerts(*, dry_run: bool = False, force: bool = False) -> dict[str, int]:
    if not dry_run and not force and not getattr(settings, "ALERT_EMAILS_ENABLED", False):
        return {"checked": 0, "matched": 0, "sent": 0, "skipped": 1}

    checked = matched = sent = 0
    subscriptions = AlertSubscription.objects.filter(is_active=True).select_related("location")
    for subscription in subscriptions:
        checked += 1
        candidate = find_alert_candidate(subscription)
        if not candidate:
            continue
        matched += 1
        if not dry_run:
            subject, body = build_alert_email(candidate)
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [subscription.email],
                fail_silently=False,
            )
            subscription.last_sent_at = timezone.now()
            subscription.save(update_fields=["last_sent_at", "updated_at"])
        sent += 1
    return {"checked": checked, "matched": matched, "sent": sent, "skipped": 0}
