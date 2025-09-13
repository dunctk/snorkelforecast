"""
OSM Spot models for worldwide snorkeling location discovery.

This module contains models for storing and managing OSM-derived
snorkeling spots with confidence scoring. Can be upgraded to GeoDjango later.
"""

from django.db import models
from django.utils import timezone


class OSMSpot(models.Model):
    """OSM-derived snorkeling spot with spatial data and confidence scoring."""

    OSM_TYPES = (("n", "node"), ("w", "way"), ("r", "relation"))

    # Source tracking
    source = models.CharField(
        max_length=16, default="osm", help_text="Data source (osm, user, wikidata)"
    )

    # OSM identifiers
    osm_type = models.CharField(
        max_length=1, choices=OSM_TYPES, null=True, blank=True, help_text="OSM element type"
    )
    osm_id = models.BigIntegerField(
        null=True, blank=True, db_index=True, help_text="OSM element ID"
    )

    # Basic information
    name = models.CharField(max_length=255, blank=True, help_text="Spot name from OSM")
    tags = models.JSONField(default=dict, help_text="All OSM tags as JSON")

    # Spatial data (upgrade to GeoDjango PointField later)
    latitude = models.FloatField(help_text="Latitude in WGS84")
    longitude = models.FloatField(help_text="Longitude in WGS84")

    # Snorkeling confidence score (0-1)
    confidence = models.FloatField(default=0.5, help_text="Snorkeling suitability score (0-1)")

    # Administrative data
    country_code = models.CharField(max_length=3, blank=True, help_text="ISO country code")
    region = models.CharField(max_length=100, blank=True, help_text="Administrative region")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_osm_update = models.DateTimeField(
        null=True, blank=True, help_text="Last time this spot was updated from OSM"
    )

    # Verification and user feedback
    is_verified = models.BooleanField(
        default=False, help_text="Manually verified as snorkeling spot"
    )
    user_votes = models.IntegerField(default=0, help_text="Number of user upvotes")
    user_flags = models.IntegerField(default=0, help_text="Number of user flags/reports")

    class Meta:
        unique_together = [("osm_type", "osm_id")]
        indexes = [
            models.Index(fields=["confidence"]),
            models.Index(fields=["country_code"]),
            models.Index(fields=["is_verified"]),
            models.Index(fields=["source"]),
            # Spatial index is automatically created for PointField
        ]

    def __str__(self):
        return f"{self.name or 'Unnamed'} ({self.get_osm_type_display()}:{self.osm_id})"

    @property
    def osm_url(self):
        """Return OSM browse URL for this element."""
        if self.osm_type and self.osm_id:
            return f"https://www.openstreetmap.org/{self.osm_type}{self.osm_id}"
        return None

    # latitude and longitude are now direct fields

    def update_confidence(self):
        """Recalculate confidence score based on tags and context."""
        score = 0.0
        tags = self.tags or {}

        # Direct snorkeling/diving indicators
        if tags.get("sport") == "scuba_diving" and tags.get("scuba_diving:divespot") == "yes":
            score += 0.6  # Strong indicator

        # Natural features
        if tags.get("natural") == "reef":
            score += 0.4  # Reefs are snorkeling magnets
        if tags.get("natural") == "beach":
            score += 0.2  # Beaches provide access

        # Infrastructure indicators
        if tags.get("amenity") == "dive_centre":
            score += 0.3  # Nearby dive infrastructure
        if tags.get("shop") == "scuba_diving":
            score += 0.2  # Scuba shop nearby

        # Marine protected areas
        if tags.get("boundary") == "national_park" or tags.get("boundary") == "protected_area":
            if "marine" in str(tags).lower():
                score += 0.3

        # Leisure activities near water
        if tags.get("leisure") in ["beach_resort", "marina"]:
            score += 0.3  # Marinas provide excellent water access for snorkeling

        # Penalize if clearly not snorkeling-related
        if tags.get("highway") or tags.get("building"):
            score -= 0.5

        # Clamp to 0-1 range
        self.confidence = max(0.0, min(1.0, score))
        self.save(update_fields=["confidence", "updated_at"])


class ImportTile(models.Model):
    """Tile for managing OSM import queue with retry logic."""

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("running", "Running"),
        ("done", "Done"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),  # No data in tile
    )

    # Tile coordinates (Web Mercator)
    z = models.IntegerField(help_text="Zoom level")
    x = models.IntegerField(help_text="Tile X coordinate")
    y = models.IntegerField(help_text="Tile Y coordinate")

    # Status and retry logic
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    retries = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=5)
    next_try_at = models.DateTimeField(null=True, blank=True)

    # Import statistics
    spots_imported = models.IntegerField(
        default=0, help_text="Number of spots imported from this tile"
    )
    import_duration = models.FloatField(
        null=True, blank=True, help_text="Import duration in seconds"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_error = models.TextField(blank=True, help_text="Last error message")

    class Meta:
        unique_together = [("z", "x", "y")]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["next_try_at"]),
            models.Index(fields=["z"]),
        ]

    def __str__(self):
        return f"Tile {self.z}/{self.x}/{self.y} ({self.status})"

    @property
    def bbox(self):
        """Calculate bounding box for this tile."""
        import math

        n = 2.0**self.z
        lon1 = self.x / n * 360.0 - 180.0
        lat1 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * self.y / n))))
        lon2 = (self.x + 1) / n * 360.0 - 180.0
        lat2 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (self.y + 1) / n))))

        # Return as (south, west, north, east)
        return lat2, lon1, lat1, lon2

    def can_retry(self):
        """Check if this tile can be retried."""
        return self.retries < self.max_retries and self.status in ["pending", "failed"]

    def schedule_retry(self, delay_seconds=None):
        """Schedule next retry with exponential backoff."""
        import random

        if delay_seconds is None:
            # Exponential backoff with jitter
            delay_seconds = min(3600, 2**self.retries + random.randint(0, 60))

        self.next_try_at = timezone.now() + timezone.timedelta(seconds=delay_seconds)
        self.retries += 1
        self.save(update_fields=["next_try_at", "retries", "updated_at"])
