"""
Management command to populate high-demand Hawaii snorkeling spots.

Search Console shows SnorkelForecast already gets impressions for spot-level
Hawaii queries ("honolua bay snorkel report", "big island snorkel report
today", "hawaii snorkel report"), but we had no matching pages. This command
seeds those spots as SnorkelLocation rows so each gets its own forecast page
and is included in sitemap.xml.

Idempotent: safe to run repeatedly (skips spots that already exist).
"""

from zlib import crc32

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from ...models import SnorkelLocation

# country_slug stays "usa" to match the existing /usa/<spot>/ URL structure.
HAWAII_SPOTS = [
    {
        "name": "Hawaii",
        "city_slug": "hawaii",
        "area_slug": "",
        "region": "Hawaii",
        "latitude": 20.7500,
        "longitude": -156.5000,
        "location_type": "marine_park",
        "is_popular": True,
        "description": (
            "Hawaii snorkel report hub for comparing Maui, Oahu, Kauai and Big "
            "Island conditions before choosing a beach."
        ),
    },
    {
        "name": "Maui",
        "city_slug": "maui",
        "area_slug": "hawaii",
        "region": "Hawaii",
        "latitude": 20.7984,
        "longitude": -156.3319,
        "location_type": "island",
        "is_popular": True,
        "description": (
            "Maui is a broad island forecast hub for comparing West, Northwest "
            "and South Maui snorkel spots. Use the individual beach reports for "
            "site-level calls, because wind, swell and visibility can vary "
            "sharply between bays on the same day."
        ),
    },
    {
        "name": "Honolua Bay",
        "area_slug": "maui",
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
        "area_slug": "maui",
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
        "name": "Kaanapali Black Rock",
        "city_slug": "kaanapali-black-rock",
        "area_slug": "maui",
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
        "area_slug": "maui",
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
        "area_slug": "maui",
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
        "name": "Ulua Mokapu",
        "city_slug": "ulua-mokapu",
        "area_slug": "maui",
        "region": "Maui, Hawaii",
        "latitude": 20.6874,
        "longitude": -156.4437,
        "location_type": "reef",
        "description": (
            "Ulua and Mokapu are adjacent South Maui reef beaches with easy "
            "entries, coral shelves and frequent turtles. They are usually best "
            "early in the morning before trade winds roughen the surface."
        ),
    },
    {
        "name": "Maluaka Turtle Town",
        "city_slug": "maluaka-turtle-town",
        "area_slug": "maui",
        "region": "Maui, Hawaii",
        "latitude": 20.6496,
        "longitude": -156.4444,
        "location_type": "beach",
        "description": (
            "Maluaka, often grouped with Turtle Town, is a South Maui snorkel "
            "beach known for turtles, reef fish and morning visibility. South "
            "swell and afternoon wind can quickly make entry and visibility worse."
        ),
    },
    {
        "name": "Ahihi Kinau",
        "city_slug": "ahihi-kinau",
        "area_slug": "maui",
        "region": "Maui, Hawaii",
        "latitude": 20.6111,
        "longitude": -156.4367,
        "location_type": "marine_park",
        "description": (
            "Ahihi Kinau Natural Area Reserve protects lava-rock reef habitat on "
            "South Maui. It can be excellent in calm weather, but exposed rock "
            "entries and changing surge make low-wind, low-swell windows important."
        ),
    },
    {
        "name": "Hanauma Bay",
        "area_slug": "oahu",
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
        "area_slug": "big-island",
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
        "area_slug": "big-island",
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
            city_slug = spot.get("city_slug") or slugify(spot["name"])
            existing = SnorkelLocation.objects.filter(
                country_slug="usa", city_slug=city_slug
            ).first()
            if not existing:
                existing = SnorkelLocation.objects.filter(
                    country_slug="usa", name=spot["name"]
                ).first()

            unique_id = -int(crc32(f"usa:{city_slug}".encode("utf-8")))

            defaults = {
                "osm_id": unique_id,
                "osm_type": "manual",
                "name": spot["name"],
                "country": "USA",
                "region": spot["region"],
                "country_slug": "usa",
                "city_slug": city_slug,
                "area_slug": spot.get("area_slug", ""),
                "latitude": spot["latitude"],
                "longitude": spot["longitude"],
                "timezone": "Pacific/Honolulu",
                "description": spot["description"],
                "location_type": spot["location_type"],
                "local_region": spot.get("local_region", ""),
                "difficulty": spot.get("difficulty", ""),
                "best_time": spot.get("best_time", ""),
                "exposure": spot.get("exposure", ""),
                "shore_type": spot.get("shore_type", ""),
                "is_popular": spot.get("is_popular", False),
                "is_verified": True,
                "quality_score": 0.9,
                "source": "manual",
                "osm_tags": {},
            }

            if existing:
                changed = False
                for field, value in defaults.items():
                    if field == "osm_id" and existing.osm_id:
                        continue
                    if getattr(existing, field) != value:
                        setattr(existing, field, value)
                        changed = True
                if dry_run:
                    action = "Would update" if changed else "Would keep"
                    self.stdout.write(f"  {action}: {spot['name']} -> /usa/{city_slug}/")
                elif changed:
                    existing.save()
                    self.stdout.write(f"  Updated: {spot['name']} -> /usa/{city_slug}/")
                else:
                    self.stdout.write(f"  Skipping {spot['name']} - already current")
                skipped += 1
                continue

            location = SnorkelLocation(**defaults)

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
