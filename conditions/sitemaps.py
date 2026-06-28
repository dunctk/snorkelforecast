from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation

from .context_processors import _english_path, _spanish_path
from .models import SnorkelLocation


def _localized_sitemap_path(path: str) -> str:
    language = translation.get_language() or "en"
    if language.startswith("es"):
        return _spanish_path(path)
    return _english_path(path)


class StaticViewSitemap(Sitemap):
    """Top-level evergreen pages (homepage, countries index, search)."""

    protocol = "https"
    changefreq = "daily"
    priority = 1.0
    i18n = True
    languages = ["en", "es"]
    alternates = True
    x_default = True

    def items(self):
        return ["homepage", "best_snorkeling", "countries_index", "location_search"]

    def location(self, item):
        return _localized_sitemap_path(reverse(item))


class GuideSitemap(Sitemap):
    """Evergreen snorkeling guides (hub + articles)."""

    protocol = "https"
    changefreq = "monthly"
    priority = 0.7
    i18n = True
    languages = ["en", "es"]
    alternates = True
    x_default = True

    def items(self):
        from .guides import GUIDES

        return ["__index__"] + [g["slug"] for g in GUIDES]

    def location(self, item):
        if item == "__index__":
            return _localized_sitemap_path(reverse("guides_index"))
        return _localized_sitemap_path(reverse("guide_detail", args=[item]))


class CountrySitemap(Sitemap):
    protocol = "https"
    changefreq = "weekly"
    priority = 0.8
    i18n = True
    languages = ["en", "es"]
    alternates = True
    x_default = True

    def items(self):
        # Get unique country slugs from database
        return list(SnorkelLocation.objects.values_list("country_slug", flat=True).distinct())

    def location(self, item):
        return _localized_sitemap_path(reverse("country_directory", args=[item]))

    def lastmod(self, item):
        # Get the most recently updated location in this country
        latest_location = (
            SnorkelLocation.objects.filter(country_slug=item).order_by("-updated_at").first()
        )
        return latest_location.updated_at if latest_location else None


class LocationSitemap(Sitemap):
    protocol = "https"
    changefreq = "daily"
    priority = 0.9
    i18n = True
    languages = ["en", "es"]
    alternates = True
    x_default = True

    def items(self):
        locations = []
        for location in SnorkelLocation.objects.all():
            locations.append(
                {
                    "country_slug": location.country_slug,
                    "city_slug": location.city_slug,
                    "updated_at": location.updated_at,
                }
            )
        return locations

    def location(self, item):
        return _localized_sitemap_path(
            reverse("location_forecast", args=[item["country_slug"], item["city_slug"]])
        )

    def lastmod(self, item):
        return item["updated_at"]


class LocationSeaTemperatureSitemap(LocationSitemap):
    """Dedicated sea-temperature SEO pages for each forecast location."""

    priority = 0.8

    def location(self, item):
        return _localized_sitemap_path(
            reverse("location_sea_temperature", args=[item["country_slug"], item["city_slug"]])
        )
