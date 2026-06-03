"""
Management command to populate high-demand Hawaii snorkeling spots.

Search Console shows SnorkelForecast already gets impressions for spot-level
Hawaii queries ("honolua bay snorkel report", "big island snorkel report
today", "hawaii snorkel report"), but we had no matching pages. This command
seeds those spots as SnorkelLocation rows so each gets its own forecast page
and is included in sitemap.xml.

Idempotent: safe to run repeatedly (skips spots that already exist).
"""

from django.core.management.base import BaseCommand

from ...models import SnorkelLocation

# country_slug stays "usa" to match the existing /usa/<spot>/ URL structure.
HAWAII_SPOTS = [
    {
        "name": "Honolua Bay",
        "region": "Maui, Hawaii",
        "latitude": 21.0145,
        "longitude": -156.6385,
        "location_type": "bay",
        "description": (
            "A marine life conservation district on Maui's northwest coast, "
            "Honolua Bay is one of Hawaii's most famous snorkeling spots. The "
            "sheltered bay protects vibrant coral and reef fish, with the "
            "calmest, clearest water on summer mornings before the trade winds "
            "build."
        ),
    },
    {
        "name": "Molokini Crater",
        "region": "Maui, Hawaii",
        "latitude": 20.6314,
        "longitude": -156.4956,
        "location_type": "reef",
        "description": (
            "A crescent-shaped volcanic crater off Maui's south shore, Molokini "
            "offers some of the clearest water in Hawaii, often exceeding 30 "
            "metres of visibility. Conditions are best on calm, low-wind "
            "mornings when the crater wall shelters the inner reef."
        ),
    },
    {
        "name": "Kaanapali Beach",
        "region": "Maui, Hawaii",
        "latitude": 20.9290,
        "longitude": -156.6947,
        "location_type": "beach",
        "description": (
            "Home to Black Rock (Pu'u Keka'a), Kaanapali is one of Maui's most "
            "accessible snorkeling beaches, with turtles, reef fish and easy "
            "entry. Snorkel in the morning before afternoon wind and surf pick "
            "up along the rock."
        ),
    },
    {
        "name": "Napili Bay",
        "region": "Maui, Hawaii",
        "latitude": 21.0030,
        "longitude": -156.6670,
        "location_type": "bay",
        "description": (
            "A gentle crescent bay on West Maui, Napili is a beginner-friendly "
            "snorkeling spot with green sea turtles and reef along both points. "
            "Calmest in the early morning and during lighter summer swells."
        ),
    },
    {
        "name": "Kapalua Bay",
        "region": "Maui, Hawaii",
        "latitude": 21.0008,
        "longitude": -156.6660,
        "location_type": "bay",
        "description": (
            "Sheltered by two reef-fringed points, Kapalua Bay is one of Maui's "
            "calmest and most protected snorkeling beaches, ideal for families "
            "and beginners. Best visibility comes on low-wind mornings."
        ),
    },
    {
        "name": "Hanauma Bay",
        "region": "Oahu, Hawaii",
        "latitude": 21.2690,
        "longitude": -157.6938,
        "location_type": "marine_park",
        "description": (
            "A protected marine life conservation area inside a volcanic cone on "
            "Oahu, Hanauma Bay is Hawaii's most popular snorkeling spot. The "
            "shallow inner reef stays calm in most conditions; aim for an early "
            "slot when water is clearest and crowds are thinnest."
        ),
    },
    {
        "name": "Kealakekua Bay",
        "region": "Big Island, Hawaii",
        "latitude": 19.4790,
        "longitude": -155.9300,
        "location_type": "bay",
        "description": (
            "A marine sanctuary on the Big Island's Kona coast, Kealakekua Bay "
            "has some of Hawaii's healthiest coral and clearest water. The bay "
            "is most protected and snorkel-ready on calm, low-wind mornings."
        ),
    },
    {
        "name": "Two Step Honaunau",
        "region": "Big Island, Hawaii",
        "latitude": 19.4200,
        "longitude": -155.9130,
        "location_type": "reef",
        "description": (
            "Next to Pu'uhonua o Honaunau on the Big Island, Two Step is a "
            "celebrated Kona-coast snorkeling site with an easy lava-ledge entry, "
            "thriving reef and frequent dolphins. Go early for the calmest, "
            "clearest conditions."
        ),
    },
]


class Command(BaseCommand):
    help = "Populate high-demand Hawaii snorkeling spots as forecast pages"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without writing to the database",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        created = skipped = 0

        for spot in HAWAII_SPOTS:
            city_slug = spot["name"].lower().replace(" ", "-").replace("'", "")
            existing = SnorkelLocation.objects.filter(
                country_slug="usa", city_slug=city_slug
            ).first()
            if existing:
                self.stdout.write(f"  Skipping {spot['name']} - already exists")
                skipped += 1
                continue

            unique_id = -abs(hash(f"{spot['name']}_hawaii")) % 90000000 - 1000000

            location = SnorkelLocation(
                osm_id=unique_id,
                osm_type="manual",
                name=spot["name"],
                country="USA",
                region=spot["region"],
                country_slug="usa",
                city_slug=city_slug,
                latitude=spot["latitude"],
                longitude=spot["longitude"],
                timezone="Pacific/Honolulu",
                description=spot["description"],
                location_type=spot["location_type"],
                is_popular=False,
                is_verified=True,
                quality_score=0.9,
                source="manual",
                osm_tags={},
            )

            if dry_run:
                self.stdout.write(f"  Would create: {spot['name']} -> /usa/{city_slug}/")
                created += 1
            else:
                location.save()
                self.stdout.write(f"  Created: {spot['name']} -> /usa/{city_slug}/")
                created += 1

        self.stdout.write("\n" + "=" * 60)
        msg = f"Created {created} Hawaii spots, skipped {skipped}"
        self.stdout.write(self.style.SUCCESS(msg) if not dry_run else msg)
