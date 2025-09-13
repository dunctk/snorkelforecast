from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import SnorkelLocation


class CountrySitemap(Sitemap):
    protocol = "https"
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Get unique country slugs from database
        return list(SnorkelLocation.objects.values_list("country_slug", flat=True).distinct())

    def location(self, item):
        return reverse("country_directory", args=[item])

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
        return reverse("location_forecast", args=[item["country_slug"], item["city_slug"]])

    def lastmod(self, item):
        return item["updated_at"]
