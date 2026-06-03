"""Submit all site URLs to IndexNow so search engines crawl them quickly.

IndexNow instantly notifies Bing, Yandex, DuckDuckGo, Seznam and Naver of new or
updated URLs (it is the modern replacement for the now-removed sitemap "ping"
endpoints). Google does not consume IndexNow, but these engines do and several AI
search products are built on Bing's index.

Builds the URL list from the same sources as sitemap.xml (static pages, guides,
countries, locations). Idempotent and safe to run on every deploy.
"""

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

from ...guides import GUIDES
from ...models import SnorkelLocation

ENDPOINT = "https://api.indexnow.org/indexnow"


class Command(BaseCommand):
    help = "Submit all site URLs to IndexNow (Bing/Yandex/DuckDuckGo/etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="List URLs without submitting"
        )

    def _all_paths(self):
        paths = ["/", reverse("countries_index"), reverse("location_search"),
                 reverse("guides_index")]
        paths += [reverse("guide_detail", args=[g["slug"]]) for g in GUIDES]
        seen_countries = set()
        for country_slug, city_slug in SnorkelLocation.objects.values_list(
            "country_slug", "city_slug"
        ):
            if country_slug not in seen_countries:
                seen_countries.add(country_slug)
                paths.append(f"/{country_slug}/")
            paths.append(f"/{country_slug}/{city_slug}/")
        return paths

    def handle(self, *args, **options):
        base = getattr(settings, "SITE_BASE_URL", "https://snorkelforecast.com").rstrip("/")
        key = getattr(settings, "INDEXNOW_KEY", "")
        host = base.split("://", 1)[-1]

        if not key:
            self.stderr.write("INDEXNOW_KEY is not set; skipping IndexNow submission.")
            return

        urls = [base + p for p in self._all_paths()]
        self.stdout.write(f"Prepared {len(urls)} URLs for IndexNow ({host}).")

        if options["dry_run"]:
            for u in urls[:10]:
                self.stdout.write("  " + u)
            self.stdout.write(f"  ... ({len(urls)} total)")
            return

        # IndexNow accepts up to 10,000 URLs per request; batch conservatively.
        batch_size = 1000
        submitted = 0
        with httpx.Client(timeout=20.0) as client:
            for i in range(0, len(urls), batch_size):
                batch = urls[i : i + batch_size]
                payload = {
                    "host": host,
                    "key": key,
                    "keyLocation": f"{base}/{key}.txt",
                    "urlList": batch,
                }
                try:
                    resp = client.post(ENDPOINT, json=payload)
                    self.stdout.write(
                        f"  Batch {i // batch_size + 1}: {len(batch)} URLs -> HTTP {resp.status_code}"
                    )
                    if resp.status_code in (200, 202):
                        submitted += len(batch)
                except httpx.HTTPError as e:  # pragma: no cover - network dependent
                    self.stderr.write(f"  Batch {i // batch_size + 1} failed: {e!r}")

        self.stdout.write(self.style.SUCCESS(f"IndexNow: submitted {submitted}/{len(urls)} URLs."))
