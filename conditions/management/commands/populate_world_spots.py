"""Seed the curated worldwide snorkeling spots from conditions/world_spots.py.

Idempotent: existing (country_slug, city_slug) pairs are skipped, so this is
safe to run repeatedly and on every deploy. New spots become forecast pages and
sitemap entries automatically.
"""

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.utils.text import slugify

from ...models import SnorkelLocation
from ...world_spots import iter_spots


class Command(BaseCommand):
    help = "Populate curated worldwide snorkeling spots as forecast pages"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without writing to the database",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        created = skipped = errored = 0

        for country_slug_key, country_name, timezone, spot in iter_spots():
            name, region, lat, lon, loc_type, description = spot
            # Clean URL slugs derived from display names (keeps one page per
            # country even when spots are grouped by timezone internally).
            country_slug = slugify(country_name)
            city_slug = slugify(name)

            if SnorkelLocation.objects.filter(
                country_slug=country_slug, city_slug=city_slug
            ).exists():
                skipped += 1
                continue

            # Deterministic, distinct negative OSM id range for world spots.
            unique_id = -(abs(hash(f"world:{name}:{country_name}")) % 800000000) - 100000000

            location = SnorkelLocation(
                osm_id=unique_id,
                osm_type="manual",
                name=name,
                country=country_name,
                region=region,
                country_slug=country_slug,
                city_slug=city_slug,
                latitude=lat,
                longitude=lon,
                timezone=timezone,
                description=description,
                location_type=loc_type if loc_type in dict(SnorkelLocation._meta.get_field(
                    "location_type").choices) else "other",
                is_popular=False,
                is_verified=True,
                quality_score=0.85,
                source="curated",
                osm_tags={},
            )

            if dry_run:
                self.stdout.write(f"  Would create: {name} -> /{country_slug}/{city_slug}/")
                created += 1
                continue

            try:
                location.save()
                created += 1
            except IntegrityError as e:
                # Most likely an osm_id collision; nudge the id and retry once.
                try:
                    location.osm_id = unique_id - 1
                    location.save()
                    created += 1
                except IntegrityError:
                    self.stderr.write(f"  Skipping {name} (integrity error: {e})")
                    errored += 1

        self.stdout.write("\n" + "=" * 60)
        msg = f"World spots: created {created}, skipped {skipped}, errored {errored}"
        self.stdout.write(self.style.SUCCESS(msg) if not dry_run else msg)
