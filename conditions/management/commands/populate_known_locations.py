"""
Management command to populate database with known snorkeling locations.

This command adds curated snorkeling locations to the database when OSM is unavailable
or for critical locations that should always be available.
"""

from django.core.management.base import BaseCommand
from ...models import SnorkelLocation


class Command(BaseCommand):
    help = "Populate database with known snorkeling locations"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be populated without actually doing it",
        )
        parser.add_argument(
            "--country",
            type=str,
            help="Populate locations for specific country only",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        country_filter = options.get("country")

        # Curated snorkeling locations worldwide
        known_locations = [
            # Spain
            {
                "name": "Costa Brava",
                "country": "Spain",
                "region": "Catalonia",
                "latitude": 41.8205,
                "longitude": 3.0726,
                "description": "Rugged coastline with crystal clear waters and rocky coves",
                "location_type": "coastline",
                "timezone": "Europe/Madrid",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.9,
            },
            {
                "name": "Costa del Sol",
                "country": "Spain",
                "region": "Andalusia",
                "latitude": 36.7213,
                "longitude": -4.4214,
                "description": "Sunny beaches with excellent visibility and marine life",
                "location_type": "beach",
                "timezone": "Europe/Madrid",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.9,
            },
            {
                "name": "Ibiza",
                "country": "Spain",
                "region": "Balearic Islands",
                "latitude": 38.9067,
                "longitude": 1.4206,
                "description": "Party island with pristine beaches and clear waters",
                "location_type": "beach",
                "timezone": "Europe/Madrid",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.8,
            },
            # Greece
            {
                "name": "Mykonos",
                "country": "Greece",
                "region": "Cyclades",
                "latitude": 37.4467,
                "longitude": 25.3289,
                "description": "Aegean island with stunning beaches and clear waters",
                "location_type": "beach",
                "timezone": "Europe/Athens",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.9,
            },
            {
                "name": "Crete",
                "country": "Greece",
                "region": "Crete",
                "latitude": 35.2401,
                "longitude": 24.8093,
                "description": "Largest Greek island with diverse snorkeling spots",
                "location_type": "coastline",
                "timezone": "Europe/Athens",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.9,
            },
            {
                "name": "Corfu",
                "country": "Greece",
                "region": "Ionian Islands",
                "latitude": 39.6243,
                "longitude": 19.9217,
                "description": "Green island with beautiful beaches and coral reefs",
                "location_type": "beach",
                "timezone": "Europe/Athens",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.8,
            },
            # Turkey
            {
                "name": "Antalya",
                "country": "Turkey",
                "region": "Mediterranean",
                "latitude": 36.8969,
                "longitude": 30.7133,
                "description": "Turkish Riviera with excellent snorkeling conditions",
                "location_type": "coastline",
                "timezone": "Europe/Istanbul",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.8,
            },
            {
                "name": "Bodrum",
                "country": "Turkey",
                "region": "Aegean",
                "latitude": 37.0344,
                "longitude": 27.4306,
                "description": "Historic peninsula with crystal clear waters",
                "location_type": "coastline",
                "timezone": "Europe/Istanbul",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.8,
            },
            # Croatia
            {
                "name": "Hvar",
                "country": "Croatia",
                "region": "Dalmatia",
                "latitude": 43.1729,
                "longitude": 16.4411,
                "description": "Lavender island with pristine Adriatic waters",
                "location_type": "island",
                "timezone": "Europe/Zagreb",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.9,
            },
            {
                "name": "Krka National Park",
                "country": "Croatia",
                "region": "Dalmatia",
                "latitude": 43.8667,
                "longitude": 15.9667,
                "description": "Freshwater snorkeling in crystal clear rivers and lakes",
                "location_type": "river",
                "timezone": "Europe/Zagreb",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.8,
            },
            # USA
            {
                "name": "Big Sur",
                "country": "USA",
                "region": "California",
                "latitude": 36.2704,
                "longitude": -121.8081,
                "description": "Rugged Pacific coastline with diverse marine life",
                "location_type": "coastline",
                "timezone": "America/Los_Angeles",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.8,
            },
            {
                "name": "Florida Keys",
                "country": "USA",
                "region": "Florida",
                "latitude": 24.5557,
                "longitude": -81.7840,
                "description": "Chain of islands with world-famous coral reefs",
                "location_type": "reef",
                "timezone": "America/New_York",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.9,
            },
            # Mexico
            {
                "name": "Cancun",
                "country": "Mexico",
                "region": "Quintana Roo",
                "latitude": 21.1619,
                "longitude": -86.8515,
                "description": "Caribbean beaches with excellent snorkeling",
                "location_type": "beach",
                "timezone": "America/Cancun",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.8,
            },
            {
                "name": "Playa del Carmen",
                "country": "Mexico",
                "region": "Quintana Roo",
                "latitude": 20.6296,
                "longitude": -87.0739,
                "description": "Gateway to the Mesoamerican Barrier Reef",
                "location_type": "reef",
                "timezone": "America/Cancun",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.9,
            },
            # Thailand
            {
                "name": "Phuket",
                "country": "Thailand",
                "region": "Southern Thailand",
                "latitude": 7.8804,
                "longitude": 98.3923,
                "description": "Andaman Sea island with coral reefs and marine life",
                "location_type": "island",
                "timezone": "Asia/Bangkok",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.8,
            },
            {
                "name": "Koh Samui",
                "country": "Thailand",
                "region": "Southern Thailand",
                "latitude": 9.5120,
                "longitude": 100.0136,
                "description": "Gulf of Thailand island with clear waters",
                "location_type": "island",
                "timezone": "Asia/Bangkok",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.8,
            },
            # Indonesia
            {
                "name": "Bali",
                "country": "Indonesia",
                "region": "Bali",
                "latitude": -8.3405,
                "longitude": 115.0920,
                "description": "Island of the Gods with excellent snorkeling spots",
                "location_type": "coastline",
                "timezone": "Asia/Makassar",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.9,
            },
            {
                "name": "Komodo Island",
                "country": "Indonesia",
                "region": "East Nusa Tenggara",
                "latitude": -8.5586,
                "longitude": 119.4896,
                "description": "Home to the famous Komodo dragons and pristine reefs",
                "location_type": "island",
                "timezone": "Asia/Makassar",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.9,
            },
            # Australia
            {
                "name": "Great Barrier Reef",
                "country": "Australia",
                "region": "Queensland",
                "latitude": -16.2864,
                "longitude": 145.6983,
                "description": "World's largest coral reef system",
                "location_type": "reef",
                "timezone": "Australia/Brisbane",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 1.0,
            },
            {
                "name": "Sydney Harbour",
                "country": "Australia",
                "region": "New South Wales",
                "latitude": -33.8688,
                "longitude": 151.2093,
                "description": "Urban snorkeling in one of the world's most beautiful harbors",
                "location_type": "marine_park",
                "timezone": "Australia/Sydney",
                "is_popular": True,
                "is_verified": True,
                "quality_score": 0.7,
            },
        ]

        if country_filter:
            known_locations = [
                loc for loc in known_locations if loc["country"].lower() == country_filter.lower()
            ]

        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made to the database")
            self.stdout.write("=" * 60)

        total_created = 0
        total_skipped = 0

        for location_data in known_locations:
            # Check if location already exists (by name and country)
            existing = SnorkelLocation.objects.filter(
                name=location_data["name"], country=location_data["country"]
            ).first()

            if existing:
                self.stdout.write(f"  Skipping {location_data['name']} - already exists")
                total_skipped += 1
                continue

            # Generate unique negative OSM ID for manual locations
            unique_id = -hash(f"{location_data['name']}_{location_data['country']}") % 10000000

            location = SnorkelLocation(
                osm_id=unique_id,
                osm_type="manual",
                name=location_data["name"],
                country=location_data["country"],
                region=location_data["region"],
                country_slug=location_data["country"].lower().replace(" ", "-"),
                city_slug=location_data["name"].lower().replace(" ", "-"),
                latitude=location_data["latitude"],
                longitude=location_data["longitude"],
                timezone=location_data["timezone"],
                description=location_data["description"],
                location_type=location_data["location_type"],
                is_popular=location_data["is_popular"],
                is_verified=location_data["is_verified"],
                quality_score=location_data["quality_score"],
                source="manual",
                osm_tags={},
            )

            if dry_run:
                self.stdout.write(
                    f"  Would create: {location_data['name']}, {location_data['country']}"
                )
                total_created += 1
            else:
                location.save()
                self.stdout.write(f"  Created: {location.name}, {location.country}")
                total_created += 1

        self.stdout.write("\n" + "=" * 60)
        if dry_run:
            self.stdout.write(
                f"DRY RUN COMPLETE: Would create {total_created} locations, skipped {total_skipped}"
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"POPULATION COMPLETE: Created {total_created} locations, skipped {total_skipped}"
                )
            )
