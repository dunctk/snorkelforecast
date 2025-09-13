"""
OpenStreetMap integration for discovering snorkeling locations worldwide.

Uses Overpass API to query OSM for beaches, dive sites, marine parks, and other
snorkeling-relevant locations.
"""

from __future__ import annotations

import logging
import time
import os
from typing import List, Dict, Any, Optional
import httpx
from django.conf import settings
from django.core.cache import cache
from slugify import slugify

from .models import SnorkelLocation

logger = logging.getLogger(__name__)

# Overpass API endpoint
OVERPASS_URL = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")

# Cache settings from Django settings
OSM_CACHE_TTL = getattr(settings, "OSM_CACHE_TTL", 86400)  # 24 hours
OSM_REQUEST_DELAY = getattr(settings, "OSM_REQUEST_DELAY", 1.0)  # seconds between requests

# Snorkeling-relevant OSM tags and their location types
SNORKELING_TAGS = {
    # Natural features
    "natural": {
        "beach": "beach",
        "coastline": "coastline",
        "reef": "reef",
    },
    # Amenities
    "amenity": {
        "beach_resort": "beach",
    },
    # Tourism
    "tourism": {
        "beach": "beach",
    },
    # Leisure
    "leisure": {
        "beach_resort": "beach",
        "marina": "marina",
    },
    # Waterway
    "waterway": {
        "river": "river",
    },
    # Place types
    "place": {
        "island": "island",
        "islet": "island",
    },
    # Boundary (for marine parks)
    "boundary": {
        "national_park": "marine_park",
        "protected_area": "marine_park",
    },
}


class OSMService:
    """Service for querying OpenStreetMap data for snorkeling locations."""

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)

    def __del__(self):
        """Clean up HTTP client."""
        try:
            self.client.close()
        except Exception:
            pass

    def search_locations(
        self,
        query: str = "",
        bbox: Optional[List[float]] = None,
        limit: int = 100,
        country: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for snorkeling locations using Overpass API.

        Args:
            query: Search query (name or location)
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            limit: Maximum number of results
            country: Country name to filter results

        Returns:
            List of location dictionaries with OSM data
        """
        cache_key = f"osm_search:{query}:{bbox}:{country}:{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Build Overpass query
        query_parts = []

        # Add location filter if country specified
        if country:
            query_parts.append(f'country="{country}"')

        # Add name filter if query specified
        if query:
            query_parts.append(f'name~"{query}"')

        # Build union of all snorkeling-relevant tags
        tag_queries = []
        for key, values in SNORKELING_TAGS.items():
            for value, location_type in values.items():
                tag_query = f'node["{key}"="{value}"]'
                if bbox:
                    tag_query += f"({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]})"
                tag_queries.append(tag_query)

                # Also search ways and relations
                tag_query = f'way["{key}"="{value}"]'
                if bbox:
                    tag_query += f"({bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]})"
                tag_queries.append(tag_query)

        overpass_query = f"""
        [out:json][timeout:25];
        (
          {";".join(tag_queries)};
        );
        out center meta {limit};
        """

        try:
            # Rate limiting
            time.sleep(OSM_REQUEST_DELAY)

            response = self.client.post(OVERPASS_URL, data={"data": overpass_query})
            response.raise_for_status()

            data = response.json()
            locations = self._process_osm_response(data)

            # Cache results
            cache.set(cache_key, locations, OSM_CACHE_TTL)

            return locations

        except Exception as e:
            logger.error(f"OSM search failed: {e}")
            return []

    def get_location_details(self, osm_id: int, osm_type: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific OSM location.

        Args:
            osm_id: OpenStreetMap ID
            osm_type: OSM element type (node, way, relation)

        Returns:
            Location details dictionary or None if not found
        """
        cache_key = f"osm_details:{osm_type}:{osm_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Build query for specific element
        if osm_type == "node":
            query = f"node({osm_id});out meta;"
        elif osm_type == "way":
            query = f"way({osm_id});out center meta;"
        elif osm_type == "relation":
            query = f"relation({osm_id});out center meta;"
        else:
            return None

        overpass_query = f"[out:json][timeout:25];{query}"

        try:
            # Rate limiting
            time.sleep(OSM_REQUEST_DELAY)

            response = self.client.post(OVERPASS_URL, data={"data": overpass_query})
            response.raise_for_status()

            data = response.json()
            if data.get("elements"):
                location = self._process_osm_element(data["elements"][0])
                cache.set(cache_key, location, OSM_CACHE_TTL)
                return location

        except Exception as e:
            logger.error(f"OSM details fetch failed for {osm_type}:{osm_id}: {e}")

        return None

    def _process_osm_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Overpass API response into location dictionaries."""
        locations = []

        for element in data.get("elements", []):
            location = self._process_osm_element(element)
            if location:
                locations.append(location)

        return locations

    def _process_osm_element(self, element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single OSM element into a location dictionary."""
        try:
            # Get coordinates (handle both nodes and ways/relations with center)
            if element["type"] == "node":
                lat = element["lat"]
                lon = element["lon"]
            elif "center" in element:
                lat = element["center"]["lat"]
                lon = element["center"]["lon"]
            else:
                return None

            # Determine location type from tags
            location_type = "other"
            tags = element.get("tags", {})

            for key, values in SNORKELING_TAGS.items():
                if key in tags and tags[key] in values:
                    location_type = values[tags[key]]
                    break

            # Extract name
            name = (
                tags.get("name")
                or tags.get("name:en")
                or tags.get("alt_name")
                or f"{location_type.title()} at {lat:.4f}, {lon:.4f}"
            )

            # Extract country/region info
            country = tags.get("addr:country") or tags.get("country") or "Unknown"
            region = tags.get("addr:state") or tags.get("addr:region") or tags.get("region") or ""

            # Generate slugs
            country_slug = slugify(country.lower())
            city_slug = slugify(name.lower())

            return {
                "osm_id": element["id"],
                "osm_type": element["type"],
                "name": name,
                "country": country,
                "region": region,
                "country_slug": country_slug,
                "city_slug": city_slug,
                "latitude": lat,
                "longitude": lon,
                "location_type": location_type,
                "description": tags.get("description") or tags.get("note") or "",
                "osm_tags": tags,
                "source": "osm",
            }

        except (KeyError, TypeError) as e:
            logger.warning(f"Failed to process OSM element: {e}")
            return None

    def create_or_update_location(self, osm_data: Dict[str, Any]) -> SnorkelLocation:
        """
        Create or update a SnorkelLocation from OSM data.

        Args:
            osm_data: Location data from OSM

        Returns:
            SnorkelLocation instance
        """
        location, created = SnorkelLocation.objects.get_or_create(
            osm_id=osm_data["osm_id"],
            osm_type=osm_data["osm_type"],
            defaults={
                "name": osm_data["name"],
                "country": osm_data["country"],
                "region": osm_data["region"],
                "country_slug": osm_data["country_slug"],
                "city_slug": osm_data["city_slug"],
                "latitude": osm_data["latitude"],
                "longitude": osm_data["longitude"],
                "location_type": osm_data["location_type"],
                "description": osm_data["description"],
                "osm_tags": osm_data["osm_tags"],
                "source": osm_data["source"],
                "timezone": self._detect_timezone(osm_data["latitude"], osm_data["longitude"]),
            },
        )

        if not created:
            # Update existing location with latest data
            for field in ["name", "country", "region", "description", "osm_tags"]:
                if field in osm_data:
                    setattr(location, field, osm_data[field])
            location.save()

        return location

    def _detect_timezone(self, lat: float, lon: float) -> str:
        """
        Detect timezone for coordinates.

        This is a simplified implementation. In production, you might want to use
        a more sophisticated timezone detection service.
        """
        # For now, return UTC - in a real implementation you'd use a timezone API
        # or library like timezonefinder
        return "UTC"


# Global service instance
osm_service = OSMService()
