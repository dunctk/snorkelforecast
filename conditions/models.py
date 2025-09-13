from __future__ import annotations

from django.db import models


class SnorkelLocation(models.Model):
    """Dynamic snorkeling locations sourced from OpenStreetMap and user submissions.

    Supports both popular curated locations and dynamically discovered locations.
    """

    objects = models.Manager()

    # OSM data for uniqueness and attribution
    osm_id = models.BigIntegerField(unique=True, help_text="OpenStreetMap node/way/relation ID")
    osm_type = models.CharField(
        max_length=10,
        choices=[("node", "Node"), ("way", "Way"), ("relation", "Relation")],
        help_text="OpenStreetMap element type",
    )

    # Location identifiers (for URL compatibility with existing ForecastHour model)
    country_slug = models.CharField(max_length=64, db_index=True)
    city_slug = models.CharField(max_length=64, db_index=True)

    # Human-readable names
    name = models.CharField(max_length=200, help_text="Display name of the location")
    country = models.CharField(max_length=100, help_text="Country name")
    region = models.CharField(max_length=100, blank=True, help_text="Region/state/province")

    # Geographic data
    latitude = models.FloatField(help_text="Latitude in decimal degrees")
    longitude = models.FloatField(help_text="Longitude in decimal degrees")

    # Location metadata
    timezone = models.CharField(max_length=50, default="UTC", help_text="IANA timezone identifier")
    description = models.TextField(blank=True, help_text="Description of the snorkeling location")

    # Categorization
    location_type = models.CharField(
        max_length=50,
        choices=[
            ("beach", "Beach"),
            ("cove", "Cove"),
            ("bay", "Bay"),
            ("island", "Island"),
            ("reef", "Reef"),
            ("dive_site", "Dive Site"),
            ("marine_park", "Marine Park"),
            ("other", "Other"),
        ],
        default="beach",
        help_text="Type of snorkeling location",
    )

    # Popularity and curation
    is_popular = models.BooleanField(default=False, help_text="Featured as popular location")
    is_verified = models.BooleanField(default=False, help_text="Manually verified for quality")
    quality_score = models.FloatField(
        default=0.0, help_text="Quality score based on reviews/ratings"
    )

    # Metadata
    source = models.CharField(
        max_length=50, default="osm", help_text="Data source (osm, user, etc.)"
    )
    osm_tags = models.JSONField(default=dict, help_text="Raw OpenStreetMap tags")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["country_slug", "city_slug"],
                name="unique_location_slugs",
            )
        ]
        indexes = [
            models.Index(fields=["country_slug", "city_slug"]),
            models.Index(fields=["is_popular", "quality_score"]),
            models.Index(fields=["location_type"]),
            models.Index(fields=["source"]),
        ]

    def __str__(self) -> str:
        return f"{self.name}, {self.country} ({self.location_type})"

    @property
    def coordinates_dict(self) -> dict:
        """Return coordinates as dict for compatibility with existing code."""
        return {"lat": self.latitude, "lon": self.longitude}

    @property
    def city(self) -> str:
        """Return the city/location name for template compatibility."""
        return self.name


class ForecastHour(models.Model):
    """Stores hourly forecast snapshots for a location to build history.

    Uniqueness is enforced per (location, time) to avoid duplicates
    when the same hour is saved multiple times.
    """

    objects = models.Manager()

    location = models.ForeignKey(
        SnorkelLocation,
        on_delete=models.CASCADE,
        related_name="forecast_hours",
        help_text="The snorkeling location this forecast is for",
        null=True,
        blank=True,
    )
    time = models.DateTimeField()

    # Keep legacy fields for backward compatibility during migration
    country_slug = models.CharField(max_length=64, blank=True)
    city_slug = models.CharField(max_length=64, blank=True)

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
                fields=["location", "time"],
                name="uniq_location_time",
            )
        ]
        indexes = [
            models.Index(fields=["location", "time"]),
            # Keep legacy indexes for migration compatibility
            models.Index(fields=["country_slug", "city_slug", "time"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - convenience only
        location_str = (
            f"{self.location.country_slug}/{self.location.city_slug}"
            if self.location
            else f"{self.country_slug}/{self.city_slug}"
        )
        return f"{location_str} @ {self.time.isoformat()} ({self.rating})"
