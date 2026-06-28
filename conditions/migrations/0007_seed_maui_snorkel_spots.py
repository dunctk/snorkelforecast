from zlib import crc32

from django.db import migrations


MAUI_SPOTS = [
    {
        "name": "Maui",
        "city_slug": "maui",
        "area_slug": "",
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
        "name": "Kapalua Bay",
        "city_slug": "kapalua-bay",
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
        "name": "Napili Bay",
        "city_slug": "napili-bay",
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
        "name": "Honolua Bay",
        "city_slug": "honolua-bay",
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
        "name": "Kaanapali Black Rock",
        "city_slug": "kaanapali-black-rock",
        "area_slug": "maui",
        "region": "Maui, Hawaii",
        "latitude": 20.9290,
        "longitude": -156.6947,
        "location_type": "beach",
        "description": (
            "Home to Black Rock, Kaanapali is one of Maui's most accessible "
            "snorkeling beaches, with turtles, reef fish and easy entry. "
            "Snorkel in the morning before afternoon wind and surf pick up "
            "along the rock."
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
        "name": "Molokini Crater",
        "city_slug": "molokini-crater",
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
]


def seed_maui_spots(apps, schema_editor):
    SnorkelLocation = apps.get_model("conditions", "SnorkelLocation")
    for spot in MAUI_SPOTS:
        defaults = {
            "osm_id": -int(crc32(f"usa:{spot['city_slug']}".encode("utf-8"))),
            "osm_type": "manual",
            "name": spot["name"],
            "country": "USA",
            "region": spot["region"],
            "area_slug": spot["area_slug"],
            "latitude": spot["latitude"],
            "longitude": spot["longitude"],
            "timezone": "Pacific/Honolulu",
            "description": spot["description"],
            "location_type": spot["location_type"],
            "is_popular": spot.get("is_popular", False),
            "is_verified": True,
            "quality_score": 0.9,
            "source": "manual",
            "osm_tags": {},
        }
        SnorkelLocation.objects.update_or_create(
            country_slug="usa",
            city_slug=spot["city_slug"],
            defaults=defaults,
        )


def unseed_maui_spots(apps, schema_editor):
    SnorkelLocation = apps.get_model("conditions", "SnorkelLocation")
    SnorkelLocation.objects.filter(
        country_slug="usa",
        city_slug__in=[spot["city_slug"] for spot in MAUI_SPOTS],
        source="manual",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("conditions", "0006_snorkellocation_area_slug"),
    ]

    operations = [
        migrations.RunPython(seed_maui_spots, unseed_maui_spots),
    ]
