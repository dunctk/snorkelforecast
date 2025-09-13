"""
Management command to import snorkeling locations from OpenStreetMap.

This command searches for snorkeling-relevant locations in popular destinations
and adds them to the database for better coverage.
"""

import time
from django.core.management.base import BaseCommand
from ...osm import osm_service
from ...models import SnorkelLocation


class Command(BaseCommand):
    help = "Import snorkeling locations from OpenStreetMap for popular destinations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without actually doing it",
        )
        parser.add_argument(
            "--country",
            type=str,
            help="Import locations for specific country only",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum locations to import per search",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        country_filter = options.get("country")
        limit = options["limit"]

        # Popular snorkeling destinations to search
        search_areas = [
            {"query": "beach", "country": "Spain", "bbox": [-9.5, 35.0, 4.3, 43.8]},  # Spain
            {"query": "beach", "country": "Greece", "bbox": [19.0, 34.8, 29.0, 41.8]},  # Greece
            {"query": "beach", "country": "Turkey", "bbox": [25.0, 35.0, 45.0, 42.0]},  # Turkey
            {"query": "beach", "country": "Croatia", "bbox": [13.0, 42.0, 19.5, 46.0]},  # Croatia
            {"query": "beach", "country": "USA", "bbox": [-125.0, 24.0, -66.0, 49.0]},  # USA
            {"query": "beach", "country": "Mexico", "bbox": [-118.0, 14.0, -86.0, 32.0]},  # Mexico
            {"query": "beach", "country": "Thailand", "bbox": [97.0, 5.0, 105.0, 20.0]},  # Thailand
            {
                "query": "beach",
                "country": "Indonesia",
                "bbox": [95.0, -11.0, 141.0, 6.0],
            },  # Indonesia
            {
                "query": "beach",
                "country": "Australia",
                "bbox": [112.0, -44.0, 154.0, -10.0],
            },  # Australia
        ]

        if country_filter:
            search_areas = [
                area for area in search_areas if area["country"].lower() == country_filter.lower()
            ]

        self.stdout.write("Note: Overpass API may be busy. If no results found, try:")
        self.stdout.write("  1. Wait a few minutes and try again")
        self.stdout.write("  2. Use a different Overpass instance")
        self.stdout.write("  3. Consider manual population for critical locations")

        total_imported = 0
        total_skipped = 0

        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made to the database")
            self.stdout.write("=" * 60)

        for area in search_areas:
            country = area["country"]
            query = area["query"]
            bbox = area.get("bbox")

            self.stdout.write(f"\nSearching {country} for '{query}' locations...")

            try:
                # Search OSM for locations
                locations = osm_service.search_locations(
                    query=query, bbox=bbox, limit=limit, country=country
                )

                self.stdout.write(f"Found {len(locations)} potential locations in {country}")

                for osm_data in locations:
                    # Check if location already exists
                    existing = SnorkelLocation.objects.filter(
                        osm_id=osm_data["osm_id"], osm_type=osm_data["osm_type"]
                    ).first()

                    if existing:
                        self.stdout.write(f"  Skipping {osm_data['name']} - already exists")
                        total_skipped += 1
                        continue

                    if dry_run:
                        self.stdout.write(
                            f"  Would import: {osm_data['name']} ({osm_data['location_type']})"
                        )
                        total_imported += 1
                    else:
                        # Create the location
                        location = osm_service.create_or_update_location(osm_data)
                        self.stdout.write(f"  Imported: {location.name} ({location.location_type})")
                        total_imported += 1

                    # Rate limiting
                    time.sleep(0.1)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error searching {country}: {e}"))

        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(
                f"DRY RUN COMPLETE: Would import {total_imported} locations, skipped {total_skipped}"
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"IMPORT COMPLETE: Imported {total_imported} locations, skipped {total_skipped}"
                )
            )
