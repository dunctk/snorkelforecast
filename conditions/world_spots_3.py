"""Third curated batch of worldwide snorkeling destinations.

Same format/conventions as world_spots.py; seeded by populate_world_spots via
iter_spots(). Focused on additional famous spots and new countries (broadening
country-page coverage) plus more depth in proven-demand regions.

Tuple format: (name, region, latitude, longitude, location_type, description)
"""

WORLD_SPOTS_3: dict[str, tuple[str, str, list]] = {
    "iceland": (
        "Iceland",
        "Atlantic/Reykjavik",
        [
            ("Silfra", "Þingvellir", 64.2558, -21.1209, "dive_site",
             "Glacial fissure between the North American and Eurasian plates with "
             "100m+ visibility in near-freezing, drysuit-only water."),
        ],
    ),
    "slovenia": (
        "Slovenia",
        "Europe/Ljubljana",
        [
            ("Piran", "Istria", 45.5283, 13.5683, "coastline",
             "Adriatic town with the Strunjan nature reserve's clear, sheltered shallows."),
        ],
    ),
    "albania": (
        "Albania",
        "Europe/Tirane",
        [
            ("Ksamil", "Vlorë", 39.7667, 20.0006, "beach",
             "Ionian islets and turquoise shallows on the Albanian Riviera near Butrint."),
        ],
    ),
    "samoa": (
        "Samoa",
        "Pacific/Apia",
        [
            ("Palolo Deep", "Upolu", -13.8200, -171.7600, "marine_park",
             "Marine reserve a short swim from Apia, with a coral drop-off in clear water."),
            ("To Sua", "Upolu", -14.0220, -171.4500, "other",
             "Famous swimming hole and nearby reef-fringed coast with clear shallows."),
        ],
    ),
    "niue": (
        "Niue",
        "Pacific/Niue",
        [
            ("Limu Pools", "Niue", -18.9667, -169.9300, "cove",
             "Coral-rock pools in some of the clearest ocean water on Earth, with sea snakes."),
        ],
    ),
    "guam": (
        "Guam",
        "Pacific/Guam",
        [
            ("Tumon Bay", "Guam", 13.5167, 144.8000, "marine_park",
             "Protected preserve with shallow reef and reef fish off the main beach strip."),
        ],
    ),
    "taiwan": (
        "Taiwan",
        "Asia/Taipei",
        [
            ("Kenting", "Pingtung", 21.9500, 120.7900, "reef",
             "Southern-tip national park with coral reefs and warm, clear water."),
            ("Xiaoliuqiu", "Pingtung", 22.3450, 120.3700, "reef",
             "Coral island famous for green turtles in shallow, snorkelable bays."),
        ],
    ),
    "south-korea": (
        "South Korea",
        "Asia/Seoul",
        [
            ("Jeju Island", "Jeju", 33.2400, 126.5600, "coastline",
             "Volcanic island with clear coves, lava arches and the famous haenyeo divers."),
        ],
    ),
    "greece": (
        "Greece",
        "Europe/Athens",
        [
            ("Lefkada", "Ionian Islands", 38.7100, 20.6400, "beach",
             "Ionian island with Porto Katsiki and turquoise, sheltered swimming bays."),
            ("Zakynthos - Navagio", "Ionian Islands", 37.8590, 20.6250, "cove",
             "Shipwreck Beach cove with vivid blue water and nearby Blue Caves."),
        ],
    ),
    "spain": (
        "Spain",
        "Europe/Madrid",
        [
            ("Medes Islands", "Catalonia", 42.0470, 3.2230, "marine_park",
             "Protected Costa Brava islets with the western Med's richest reef life."),
            ("Cabo de Palos", "Murcia", 37.6300, -0.7000, "marine_park",
             "Islas Hormigas reserve with clear water and abundant fish off Murcia."),
        ],
    ),
    "italy": (
        "Italy",
        "Europe/Rome",
        [
            ("San Vito lo Capo", "Sicily", 38.1740, 12.7360, "bay",
             "Sicilian bay with white sand and the Zingaro reserve's clear coves nearby."),
            ("Ponza", "Lazio", 40.8990, 12.9620, "cove",
             "Pontine island with sea caves and clear coves popular for snorkeling."),
        ],
    ),
    "france": (
        "France",
        "Europe/Paris",
        [
            ("Porquerolles", "Provence", 43.0000, 6.2000, "marine_park",
             "Port-Cros national park island with a marked underwater snorkel trail."),
        ],
    ),
    "mexico": (
        "Mexico",
        "America/Cancun",
        [
            ("Holbox", "Quintana Roo", 21.5500, -87.3800, "other",
             "Car-free island with summer whale sharks and shallow, calm flats."),
            ("Banco Chinchorro", "Quintana Roo", 18.5900, -87.3300, "reef",
             "Remote Caribbean atoll reserve with pristine coral and clear water."),
        ],
    ),
    "maldives": (
        "Maldives",
        "Indian/Maldives",
        [
            ("Hanifaru Bay", "Baa Atoll", 5.1700, 73.0700, "marine_park",
             "UNESCO bay where seasonal plankton draws huge groups of manta rays."),
            ("Ari Atoll", "Alif", 3.8800, 72.8300, "reef",
             "Atoll famous for whale sharks and reef-sharks over clear coral."),
        ],
    ),
    "indonesia": (
        "Indonesia",
        "Asia/Makassar",
        [
            ("Nusa Lembongan", "Bali", -8.6800, 115.4500, "reef",
             "Island off Bali with mangrove channels, coral and frequent manta rays."),
            ("Labuan Bajo", "East Nusa Tenggara", -8.4960, 119.8870, "reef",
             "Gateway to Komodo with Kanawa and Sebayur reefs in clear water."),
        ],
    ),
    "saba": (
        "Saba",
        "America/Kralendijk",
        [
            ("Saba Marine Park", "Saba", 17.6200, -63.2500, "marine_park",
             "Pristine volcanic-island marine park with healthy reef and clear water."),
        ],
    ),
    "saint-vincent-and-the-grenadines": (
        "Saint Vincent and the Grenadines",
        "America/St_Vincent",
        [
            ("Tobago Cays", "Grenadines", 12.6333, -61.3500, "marine_park",
             "Uninhabited cays with a turtle sanctuary and a horseshoe reef lagoon."),
        ],
    ),
    "dominica": (
        "Dominica",
        "America/Dominica",
        [
            ("Champagne Reef", "Saint Mark", 15.2333, -61.3667, "reef",
             "Volcanic reef where warm geothermal bubbles rise through clear water."),
        ],
    ),
    "brazil": (
        "Brazil",
        "America/Sao_Paulo",
        [
            ("Arraial do Cabo", "Rio de Janeiro", -22.9667, -42.0278, "cove",
             "The 'Brazilian Caribbean' with clear water, coves and resident turtles."),
        ],
    ),
    "cape-verde": (
        "Cape Verde",
        "Atlantic/Cape_Verde",
        [
            ("Sal", "Sal", 16.5950, -22.9100, "reef",
             "Atlantic island with calm bays, lemon sharks at Shark Bay and clear shallows."),
        ],
    ),
}


def iter_spots_3():
    for country_slug, (country_name, timezone, spots) in WORLD_SPOTS_3.items():
        for spot in spots:
            yield country_slug, country_name, timezone, spot
