"""
Management command to migrate hardcoded popular locations to database.
"""

from django.core.management.base import BaseCommand

from ...models import SnorkelLocation
from ...locations import LOCATIONS


class Command(BaseCommand):
    help = "Migrate hardcoded popular locations to SnorkelLocation database table"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be migrated without actually doing it",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made to the database")
            self.stdout.write("=" * 50)

        migrated_count = 0
        skipped_count = 0

        for country_slug, cities in LOCATIONS.items():
            for city_slug, location_data in cities.items():
                # Check if location already exists
                existing = SnorkelLocation.objects.filter(
                    country_slug=country_slug, city_slug=city_slug
                ).first()

                if existing:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping {country_slug}/{city_slug} - already exists in database"
                        )
                    )
                    skipped_count += 1
                    continue

                # Create new location with unique negative OSM ID for legacy locations
                # Use negative IDs to avoid conflicts with real OSM data
                legacy_id = -hash(f"{country_slug}/{city_slug}") % 1000000

                location = SnorkelLocation(
                    osm_id=legacy_id,
                    osm_type="manual",
                    name=location_data["city"],
                    country=location_data["country"],
                    region="",  # Can be filled in later if needed
                    country_slug=country_slug,
                    city_slug=city_slug,
                    latitude=location_data["coordinates"]["lat"],
                    longitude=location_data["coordinates"]["lon"],
                    timezone=location_data["timezone"],
                    description=location_data.get("description", ""),
                    location_type="beach",  # Default for popular locations
                    is_popular=True,
                    is_verified=True,
                    quality_score=1.0,  # High score for popular locations
                    source="legacy",
                    osm_tags={},  # Empty for legacy locations
                )

                if not dry_run:
                    location.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"Created {country_slug}/{city_slug} in database")
                    )
                else:
                    self.stdout.write(f"Would create {country_slug}/{city_slug}")

                migrated_count += 1

        self.stdout.write("=" * 50)
        if dry_run:
            self.stdout.write(f"DRY RUN COMPLETE: Would migrate {migrated_count} locations")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"MIGRATION COMPLETE: Migrated {migrated_count} locations, skipped {skipped_count}"
                )
            )
