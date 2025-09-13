"""
Management command to import OSM snorkeling spots using tile-based strategy.

This command implements a robust tile-based import system with:
- Multiple Overpass mirrors with round-robin
- Exponential backoff and retry logic
- Better OSM queries for snorkeling-specific features
- Confidence scoring for imported spots
"""

import math
import time
from typing import Tuple, Optional

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
# from django.contrib.gis.geos import Point  # Temporarily disabled

from ...models_spots import OSMSpot, ImportTile


class Command(BaseCommand):
    help = "Import OSM snorkeling spots using tile-based strategy with retry logic"

    # Overpass API endpoints (round-robin)
    ENDPOINTS = [
        "https://overpass.private.coffee/api/interpreter",
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

    # User agent for polite requests
    USER_AGENT = {"User-Agent": "SnorkelForecast/1.0 (https://snorkelforecast.com)"}

    # Improved Overpass query for snorkeling-relevant features
    QUERY_TEMPLATE = """[out:json][timeout:120];
(
  // Direct snorkeling/diving spots
  node["sport"="scuba_diving"]({bbox});
  way["sport"="scuba_diving"]({bbox});
  rel["sport"="scuba_diving"]({bbox});

  // Natural features that are snorkeling magnets
  way["natural"="reef"]({bbox});
  rel["natural"="reef"]({bbox});
  way["natural"="beach"]({bbox});
  rel["natural"="beach"]({bbox});

  // Marine protected areas (with marine in name/description)
  way["boundary"="national_park"]["name"~"marine"]({bbox});
  rel["boundary"="national_park"]["name"~"marine"]({bbox});
  way["boundary"="protected_area"]["name"~"marine"]({bbox});
  rel["boundary"="protected_area"]["name"~"marine"]({bbox});

  // Infrastructure that indicates snorkeling/diving activity
  node["amenity"="dive_centre"]({bbox});
  way["amenity"="dive_centre"]({bbox});
  node["shop"="scuba_diving"]({bbox});
  way["shop"="scuba_diving"]({bbox});

  // Leisure activities near water
  node["leisure"="beach_resort"]({bbox});
  way["leisure"="beach_resort"]({bbox});
  node["leisure"="marina"]({bbox});
  way["leisure"="marina"]({bbox});
);
out body; >; out skel qt;"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--zoom",
            type=int,
            default=7,
            help="Zoom level for tiles (default: 7, ~20k tiles globally)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10,
            help="Number of tiles to process per batch",
        )
        parser.add_argument(
            "--max-retries",
            type=int,
            default=3,
            help="Maximum retries per tile",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without making changes",
        )
        parser.add_argument(
            "--country-bbox",
            type=str,
            help="Import only tiles within country bbox (south,west,north,east)",
        )
        parser.add_argument(
            "--create-tiles",
            action="store_true",
            help="Create tile queue for specified zoom level",
        )

    def handle(self, *args, **options):
        zoom = options["zoom"]
        batch_size = options["batch_size"]
        dry_run = options["dry_run"]
        country_bbox = options.get("country_bbox")
        create_tiles = options["create_tiles"]

        if create_tiles:
            self.create_tile_queue(zoom, country_bbox)
            return

        if dry_run:
            self.stdout.write("DRY RUN - No database changes will be made")
            self.stdout.write("=" * 60)

        # Process pending tiles
        processed = 0
        successful = 0
        failed = 0

        while processed < batch_size:
            tile = self.get_next_tile()
            if not tile:
                self.stdout.write("No more tiles to process")
                break

            self.stdout.write(f"Processing tile {tile.z}/{tile.x}/{tile.y}...")

            try:
                spots_imported = self.process_tile(tile, dry_run)
                successful += 1
                tile.status = "done"
                tile.spots_imported = spots_imported
                tile.save()

                if not dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Imported {spots_imported} spots from tile {tile.z}/{tile.x}/{tile.y}"
                        )
                    )
                else:
                    self.stdout.write(
                        f"Would import {spots_imported} spots from tile {tile.z}/{tile.x}/{tile.y}"
                    )

            except Exception as e:
                failed += 1
                tile.status = "failed"
                tile.last_error = str(e)
                tile.schedule_retry()
                tile.save()

                self.stdout.write(
                    self.style.ERROR(f"✗ Failed tile {tile.z}/{tile.x}/{tile.y}: {e}")
                )

            processed += 1

        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(f"DRY RUN COMPLETE: Would process {processed} tiles")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"BATCH COMPLETE: {successful} successful, {failed} failed, {processed} total"
                )
            )

    def create_tile_queue(self, zoom: int, country_bbox: Optional[str] = None):
        """Create tile queue for the specified zoom level."""
        self.stdout.write(f"Creating tile queue for zoom level {zoom}...")

        tiles_created = 0
        tiles_skipped = 0

        # Calculate tile range
        max_tile = 2**zoom

        # Parse country bbox if provided
        bbox_filter = None
        if country_bbox:
            try:
                south, west, north, east = map(float, country_bbox.split(","))
                bbox_filter = (south, west, north, east)
                self.stdout.write(f"Filtering tiles within bbox: {bbox_filter}")
            except ValueError:
                self.stdout.write(
                    self.style.ERROR("Invalid bbox format. Use: south,west,north,east")
                )
                return

        for x in range(max_tile):
            for y in range(max_tile):
                # Skip if outside country bbox
                if bbox_filter:
                    tile_bbox = self.tile_to_bbox(zoom, x, y)
                    if not self.bboxes_overlap(tile_bbox, bbox_filter):
                        tiles_skipped += 1
                        continue

                # Create tile if it doesn't exist
                tile, created = ImportTile.objects.get_or_create(
                    z=zoom, x=x, y=y, defaults={"status": "pending"}
                )

                if created:
                    tiles_created += 1
                else:
                    tiles_skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Tile queue created: {tiles_created} new tiles, {tiles_skipped} skipped"
            )
        )

    def get_next_tile(self) -> Optional[ImportTile]:
        """Get next tile to process (pending or failed with retry available)."""
        now = timezone.now()

        # First try pending tiles
        tile = ImportTile.objects.filter(status="pending").order_by("created_at").first()

        if not tile:
            # Then try failed tiles that can be retried
            tile = (
                ImportTile.objects.filter(status="failed", retries__lt=5, next_try_at__lte=now)
                .order_by("next_try_at")
                .first()
            )

        if tile:
            tile.status = "running"
            tile.save(update_fields=["status"])

        return tile

    def process_tile(self, tile: ImportTile, dry_run: bool = False) -> int:
        """Process a single tile and import spots."""
        start_time = time.time()

        # Get tile bbox
        south, west, north, east = tile.bbox
        bbox_str = f"{south},{west},{north},{east}"

        # Build query
        query = self.QUERY_TEMPLATE.format(bbox=bbox_str)

        # Try different endpoints with round-robin
        data = None
        for i in range(len(self.ENDPOINTS)):
            endpoint_idx = (tile.retries + i) % len(self.ENDPOINTS)
            endpoint = self.ENDPOINTS[endpoint_idx]

            try:
                self.stdout.write(f"  Querying {endpoint}...")
                response = requests.post(
                    endpoint, data={"data": query}, headers=self.USER_AGENT, timeout=150
                )
                response.raise_for_status()
                data = response.json()
                break

            except Exception as e:
                self.stdout.write(f"  Endpoint {endpoint} failed: {e}")
                continue

        if not data:
            raise Exception("All Overpass endpoints failed")

        # Process OSM elements
        elements = data.get("elements", [])
        self.stdout.write(f"  Found {len(elements)} OSM elements")

        # Debug: show what elements we found
        if elements:
            for i, element in enumerate(elements[:3]):  # Show first 3 elements
                tags = element.get("tags", {})
                has_center = "center" in element
                self.stdout.write(
                    f"    Element {i + 1}: {element['type']}:{element['id']} - has_center: {has_center} - tags: {list(tags.keys())}"
                )

        spots_imported = 0

        if not dry_run:
            with transaction.atomic():
                for element in elements:
                    if self.create_or_update_spot(element):
                        spots_imported += 1
        else:
            # In dry run, just count potential spots
            for element in elements:
                lat, lon, osm_type, osm_id = self.element_to_coords(element)
                if lat is not None and lon is not None:
                    spots_imported += 1

        # Update tile statistics
        tile.import_duration = time.time() - start_time

        return spots_imported

    def create_or_update_spot(self, element: dict) -> bool:
        """Create or update an OSM spot from element data."""
        lat, lon, osm_type, osm_id = self.element_to_coords(element)
        if lat is None or lon is None:
            return False

        tags = element.get("tags", {})

        # Skip if no relevant tags
        if not self.is_snorkeling_relevant(tags):
            self.stdout.write(f"    Skipping {osm_type}:{osm_id} - not snorkeling relevant")
            return False

        # Create or update spot
        spot, created = OSMSpot.objects.get_or_create(
            osm_type=osm_type,
            osm_id=osm_id,
            defaults={
                "name": tags.get("name", ""),
                "tags": tags,
                "latitude": lat,
                "longitude": lon,
                "source": "osm",
            },
        )

        if not created:
            # Update existing spot
            spot.name = tags.get("name", spot.name)
            spot.tags = tags
            spot.latitude = lat
            spot.longitude = lon
            spot.last_osm_update = timezone.now()

        # Calculate confidence score
        spot.update_confidence()
        spot.save()

        return True

    def element_to_coords(
        self, element: dict
    ) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[int]]:
        """Convert OSM element to coordinates."""
        elem_type = element["type"][0]  # 'node', 'way', 'relation' -> 'n', 'w', 'r'
        elem_id = element["id"]

        if elem_type == "n":
            # Node: direct coordinates
            try:
                return float(element["lat"]), float(element["lon"]), elem_type, elem_id
            except (KeyError, ValueError):
                return None, None, elem_type, elem_id

        elif "center" in element:
            # Way/Relation with center from Overpass
            try:
                center = element["center"]
                return float(center["lat"]), float(center["lon"]), elem_type, elem_id
            except (KeyError, ValueError):
                return None, None, elem_type, elem_id

        return None, None, elem_type, elem_id

    def is_snorkeling_relevant(self, tags: dict) -> bool:
        """Check if OSM tags are relevant for snorkeling."""
        # Direct snorkeling/diving indicators
        if tags.get("sport") == "scuba_diving":
            return True
        if tags.get("scuba_diving:divespot") == "yes":
            return True

        # Natural features that are snorkeling magnets
        if tags.get("natural") == "reef":
            return True
        if tags.get("natural") == "beach":
            return True

        # Marine protected areas
        if tags.get("boundary") in ["national_park", "protected_area"]:
            # Check if it's marine-related
            if any("marine" in str(v).lower() for v in tags.values()):
                return True

        # Infrastructure that indicates snorkeling/diving activity
        if tags.get("amenity") == "dive_centre":
            return True
        if tags.get("shop") == "scuba_diving":
            return True

        # Leisure activities near water
        if tags.get("leisure") in ["beach_resort", "marina"]:
            return True

        return False

    @staticmethod
    def tile_to_bbox(z: int, x: int, y: int) -> Tuple[float, float, float, float]:
        """Convert tile coordinates to bbox (south, west, north, east)."""
        n = 2.0**z
        lon1 = x / n * 360.0 - 180.0
        lat1 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
        lon2 = (x + 1) / n * 360.0 - 180.0
        lat2 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))

        return lat2, lon1, lat1, lon2

    @staticmethod
    def bboxes_overlap(
        bbox1: Tuple[float, float, float, float], bbox2: Tuple[float, float, float, float]
    ) -> bool:
        """Check if two bboxes overlap."""
        south1, west1, north1, east1 = bbox1
        south2, west2, north2, east2 = bbox2

        return not (east1 < west2 or west1 > east2 or north1 < south2 or south1 > north2)
