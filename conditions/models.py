from __future__ import annotations

from django.db import models


class ForecastHour(models.Model):
    """Stores hourly forecast snapshots for a location to build history.

    Uniqueness is enforced per (country_slug, city_slug, time) to avoid duplicates
    when the same hour is saved multiple times.
    """

    objects = models.Manager()

    country_slug = models.CharField(max_length=64)
    city_slug = models.CharField(max_length=64)
    time = models.DateTimeField()

    ok = models.BooleanField(default=False)
    score = models.FloatField(default=0.0)
    rating = models.CharField(max_length=16)

    wave_height = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    sea_surface_temperature = models.FloatField(null=True, blank=True)
    sea_level_height = models.FloatField(null=True, blank=True)
    current_velocity = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["country_slug", "city_slug", "time"],
                name="uniq_location_time",
            )
        ]
        indexes = [
            models.Index(fields=["country_slug", "city_slug", "time"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return f"{self.country_slug}/{self.city_slug} @ {self.time.isoformat()} ({self.rating})"
