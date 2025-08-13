from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .locations import LOCATIONS


class CountrySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return LOCATIONS.keys()

    def location(self, item):
        return reverse("country_directory", args=[item])


class LocationSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        locations = []
        for country_slug, cities in LOCATIONS.items():
            for city_slug, _ in cities.items():
                locations.append({"country_slug": country_slug, "city_slug": city_slug})
        return locations

    def location(self, item):
        return reverse(
            "location_forecast", args=[item["country_slug"], item["city_slug"]]
        )
