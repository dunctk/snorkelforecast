"""Second curated batch of worldwide snorkeling destinations.

Same format and conventions as conditions/world_spots.py. Kept in a separate
module purely to keep each file readable; both are seeded by the
populate_world_spots management command via iter_spots().

Tuple format: (name, region, latitude, longitude, location_type, description)
"""

WORLD_SPOTS_2: dict[str, tuple[str, str, list]] = {
    "palau": (
        "Palau",
        "Pacific/Palau",
        [
            ("Jellyfish Lake", "Koror", 7.1610, 134.3760, "marine_park",
             "Marine lake where you snorkel through millions of stingless golden jellyfish."),
            ("German Channel", "Koror", 7.1500, 134.2200, "reef",
             "Famous manta-ray cleaning station amid Palau's Rock Islands reefs."),
        ],
    ),
    "cook-islands": (
        "Cook Islands",
        "Pacific/Rarotonga",
        [
            ("Aitutaki Lagoon", "Aitutaki", -18.8500, -159.7850, "reef",
             "Triangular lagoon of impossibly clear turquoise water and coral bommies."),
            ("Rarotonga", "Rarotonga", -21.2300, -159.7770, "reef",
             "Island ringed by a shallow lagoon with marine reserves snorkelable from the beach."),
        ],
    ),
    "french-polynesia": (
        "French Polynesia",
        "Pacific/Tahiti",
        [
            ("Fakarava", "Tuamotus", -16.0500, -145.6200, "reef",
             "UNESCO biosphere atoll with drift snorkeling through shark-filled passes."),
            ("Tikehau", "Tuamotus", -15.0000, -148.2300, "reef",
             "Pink-sand atoll with a manta-ray cleaning station and clear lagoon coral."),
        ],
    ),
    "vanuatu": (
        "Vanuatu",
        "Pacific/Efate",
        [
            ("Champagne Beach", "Espiritu Santo", -15.1200, 167.1100, "beach",
             "Powder-white beach with calm clear shallows and nearby blue holes."),
        ],
    ),
    "new-caledonia": (
        "New Caledonia",
        "Pacific/Noumea",
        [
            ("Île des Pins", "Loyalty", -22.6200, 167.4800, "reef",
             "Lagoon island in the world's largest barrier reef, with natural coral pools."),
        ],
    ),
    "tonga": (
        "Tonga",
        "Pacific/Tongatapu",
        [
            ("Vavaʻu", "Vavaʻu", -18.6500, -173.9800, "reef",
             "Island group famed for swimming with humpback whales and clear reef water."),
        ],
    ),
    "australia": (
        "Australia",
        "Australia/Brisbane",
        [
            ("Whitsundays", "Queensland", -20.2600, 149.0300, "reef",
             "Coral islands beside the Great Barrier Reef with fringing reef and white sand."),
            ("Byron Bay", "New South Wales", -28.6380, 153.6300, "marine_park",
             "Julian Rocks reserve with turtles, rays and grey nurse sharks in clear water."),
            ("Jervis Bay", "New South Wales", -35.1000, 150.7300, "bay",
             "Marine park with white-sand beaches and clear seagrass and reef shallows."),
            ("Ningaloo - Coral Bay", "Western Australia", -23.1430, 113.7700, "reef",
             "Sheltered bay where the Ningaloo reef sits just metres off the beach."),
        ],
    ),
    "indonesia": (
        "Indonesia",
        "Asia/Makassar",
        [
            ("Komodo - Pink Beach", "East Nusa Tenggara", -8.6700, 119.6000, "reef",
             "Pink-sand beach in Komodo park with vivid coral and reef fish offshore."),
            ("Wakatobi", "Southeast Sulawesi", -5.3300, 123.5800, "reef",
             "Remote marine park with some of the planet's healthiest, most colorful reefs."),
            ("Gili Air", "West Nusa Tenggara", -8.3600, 116.0850, "reef",
             "Quiet Gili island with turtles and coral gardens off a calm shore."),
            ("Derawan", "East Kalimantan", 2.2840, 118.2470, "reef",
             "Borneo archipelago with turtles, mantas and a stingless-jellyfish lake."),
        ],
    ),
    "philippines": (
        "Philippines",
        "Asia/Manila",
        [
            ("Boracay", "Aklan", 11.9690, 121.9270, "reef",
             "Famous white-sand island with reef snorkeling off Crocodile and Yapak."),
            ("Siquijor", "Siquijor", 9.2140, 123.5150, "reef",
             "Quiet island ringed by marine sanctuaries and clear coral shallows."),
            ("Anilao", "Batangas", 13.7600, 120.8900, "reef",
             "Macro-diving capital near Manila with rich shallow reefs."),
            ("Donsol", "Sorsogon", 12.9100, 123.6000, "other",
             "Bay where you can snorkel with seasonal whale sharks and see fireflies at night."),
        ],
    ),
    "thailand": (
        "Thailand",
        "Asia/Bangkok",
        [
            ("Koh Kradan", "Trang", 7.2670, 99.2500, "reef",
             "Andaman island with a long fringing reef snorkelable straight off the sand."),
            ("Railay", "Krabi", 8.0110, 98.8380, "bay",
             "Limestone peninsula with sheltered bays and reef around the cliffs."),
        ],
    ),
    "malaysia": (
        "Malaysia",
        "Asia/Kuala_Lumpur",
        [
            ("Mabul", "Sabah", 4.2470, 118.6300, "reef",
             "Macro-rich island beside Sipadan with shallow reefs off the stilt villages."),
            ("Langkawi", "Kedah", 6.3500, 99.8000, "reef",
             "Andaman archipelago with the Payar Island marine park's reefs and reef sharks."),
        ],
    ),
    "cambodia": (
        "Cambodia",
        "Asia/Phnom_Penh",
        [
            ("Koh Rong", "Preah Sihanouk", 10.7200, 103.2400, "reef",
             "Gulf island with clear shallows, reef patches and bioluminescent plankton."),
        ],
    ),
    "india": (
        "India",
        "Asia/Kolkata",
        [
            ("Havelock Island", "Andaman Islands", 11.9600, 93.0000, "reef",
             "Andaman island with Elephant Beach's shallow reef and clear blue water."),
            ("Lakshadweep", "Lakshadweep", 10.5670, 72.6420, "reef",
             "Coral atolls in the Arabian Sea with pristine lagoons and reef fish."),
        ],
    ),
    "japan": (
        "Japan",
        "Asia/Tokyo",
        [
            ("Okinawa - Blue Cave", "Okinawa", 26.4600, 127.8300, "dive_site",
             "Cape Maeda sea cave glowing blue, with reef fish in the clear entrance."),
        ],
    ),
    "uae": (
        "United Arab Emirates",
        "Asia/Dubai",
        [
            ("Snoopy Island", "Fujairah", 25.5050, 56.3580, "reef",
             "Fujairah's Gulf of Oman islet with reef and turtles off the beach."),
        ],
    ),
    "saudi-arabia": (
        "Saudi Arabia",
        "Asia/Riyadh",
        [
            ("Yanbu", "Al Madinah", 24.0890, 38.0640, "reef",
             "Red Sea coast with pristine, rarely-crowded fringing reefs."),
        ],
    ),
    "egypt": (
        "Egypt",
        "Africa/Cairo",
        [
            ("El Gouna", "Red Sea Governorate", 27.3940, 33.6780, "reef",
             "Red Sea resort with offshore reefs and calm lagoon snorkeling."),
            ("Safaga", "Red Sea Governorate", 26.7330, 33.9380, "reef",
             "Quiet Red Sea bay with house reefs and steady, clear water."),
        ],
    ),
    "spain": (
        "Spain",
        "Atlantic/Canary",
        [
            ("Gran Canaria", "Canary Islands", 27.8500, -15.5000, "reef",
             "Canary island with El Cabrón marine reserve and clear volcanic reefs."),
            ("La Palma", "Canary Islands", 28.6800, -17.7640, "dive_site",
             "Steep volcanic Canary island with clear Atlantic water and reef fish."),
            ("La Gomera", "Canary Islands", 28.0916, -17.1133, "cove",
             "Round Canary island with sheltered coves and clear Atlantic shallows."),
        ],
    ),
    "italy": (
        "Italy",
        "Europe/Rome",
        [
            ("Capri", "Campania", 40.5500, 14.2300, "cove",
             "Iconic island with sea caves and clear water around the Faraglioni."),
            ("Cinque Terre", "Liguria", 44.1080, 9.7270, "marine_park",
             "Protected Ligurian coast with rocky coves and clear snorkeling off the villages."),
            ("Lampedusa", "Sicily", 35.5100, 12.6100, "beach",
             "Pelagie island with Rabbit Beach's turtle nesting and crystal-clear shallows."),
            ("Tropea", "Calabria", 38.6770, 15.8970, "beach",
             "Calabrian cliff town with clear Tyrrhenian water and rocky snorkeling."),
        ],
    ),
    "greece": (
        "Greece",
        "Europe/Athens",
        [
            ("Naxos", "Cyclades", 37.1060, 25.3760, "bay",
             "Largest Cycladic island with sheltered sandy bays and clear Aegean water."),
            ("Symi", "Dodecanese", 36.6100, 27.8400, "cove",
             "Small Dodecanese island with deep, clear coves and rocky reefs."),
            ("Kos", "Dodecanese", 36.8930, 27.2880, "bay",
             "Dodecanese island with calm bays and clear shallows along long beaches."),
            ("Skiathos", "Sporades", 39.1620, 23.4900, "cove",
             "Sporades island with pine-backed coves and clear turquoise water."),
        ],
    ),
    "croatia": (
        "Croatia",
        "Europe/Zagreb",
        [
            ("Korčula", "Dubrovnik-Neretva", 42.9600, 17.1350, "cove",
             "Wooded Adriatic island with pebbly coves and clear, calm water."),
            ("Dugi Otok", "Zadar", 43.9000, 15.0500, "marine_park",
             "Island beside Kornati park with Telašćica's cliffs and clear bays."),
        ],
    ),
    "montenegro": (
        "Montenegro",
        "Europe/Podgorica",
        [
            ("Bay of Kotor", "Kotor", 42.4300, 18.6800, "bay",
             "Fjord-like Adriatic bay with sheltered, clear water and rocky shores."),
        ],
    ),
    "turkey": (
        "Turkey",
        "Europe/Istanbul",
        [
            ("Ölüdeniz", "Muğla", 36.5500, 29.1160, "bay",
             "Famous Blue Lagoon with calm, glassy turquoise water for easy snorkeling."),
        ],
    ),
    "cyprus": (
        "Cyprus",
        "Asia/Nicosia",
        [
            ("Cape Greco", "Famagusta", 34.9620, 34.0750, "marine_park",
             "National park headland with sea caves and clear water full of fish."),
            ("Coral Bay", "Paphos", 34.8580, 32.3700, "bay",
             "Sheltered Paphos bay with calm, clear shallows over rock and sand."),
        ],
    ),
    "malta": (
        "Malta",
        "Europe/Malta",
        [
            ("Blue Lagoon Comino", "Comino", 36.0150, 14.3270, "bay",
             "Brilliant turquoise lagoon between Malta and Gozo with clear, calm water."),
            ("Gozo - Dwejra", "Gozo", 36.0490, 14.1900, "dive_site",
             "Gozo's Inland Sea and reefs with exceptionally clear Mediterranean water."),
        ],
    ),
    "aruba": (
        "Aruba",
        "America/Aruba",
        [
            ("Mangel Halto", "Aruba", 12.4600, -69.9700, "reef",
             "Sheltered mangrove cove with a shallow reef and easy clear-water entry."),
            ("Boca Catalina", "Aruba", 12.5800, -70.0500, "bay",
             "Calm northwest cove with fish-filled shallows close to shore."),
        ],
    ),
    "turks-and-caicos": (
        "Turks and Caicos",
        "America/Grand_Turk",
        [
            ("Grace Bay", "Providenciales", 21.8000, -72.2000, "reef",
             "Protected reef off a famous white-sand beach with calm, clear shallows."),
            ("Smith's Reef", "Providenciales", 21.7900, -72.2300, "reef",
             "Shore-accessible reef with turtles, rays and reef fish off Provo."),
        ],
    ),
    "british-virgin-islands": (
        "British Virgin Islands",
        "America/Tortola",
        [
            ("The Baths", "Virgin Gorda", 18.4300, -64.4450, "cove",
             "Granite grottoes and clear pools forming a unique snorkeling maze."),
        ],
    ),
    "anguilla": (
        "Anguilla",
        "America/Anguilla",
        [
            ("Shoal Bay", "Anguilla", 18.2600, -63.0100, "reef",
             "Long white-sand beach with a calm fringing reef in clear shallows."),
        ],
    ),
    "dominican-republic": (
        "Dominican Republic",
        "America/Santo_Domingo",
        [
            ("Bayahibe", "La Altagracia", 18.3600, -68.8400, "reef",
             "Launch point for Catalina Island's wall and shallow coral gardens."),
        ],
    ),
    "cuba": (
        "Cuba",
        "America/Havana",
        [
            ("María la Gorda", "Pinar del Río", 21.8200, -84.4900, "reef",
             "Remote west-coast bay with pristine coral and clear Caribbean water."),
            ("Cayo Coco", "Ciego de Ávila", 22.5100, -78.5100, "reef",
             "Cay on Cuba's northern reef with calm, clear turquoise shallows."),
        ],
    ),
    "jamaica": (
        "Jamaica",
        "America/Jamaica",
        [
            ("Negril", "Westmoreland", 18.2680, -78.3450, "reef",
             "Seven Mile Beach with offshore reefs and clear west-coast water."),
        ],
    ),
    "martinique": (
        "Martinique",
        "America/Martinique",
        [
            ("Anses-d'Arlet", "Martinique", 14.4900, -61.0850, "bay",
             "Postcard village bay with turtles grazing in calm, clear shallows."),
        ],
    ),
    "guadeloupe": (
        "Guadeloupe",
        "America/Guadeloupe",
        [
            ("Pigeon Island - Cousteau", "Guadeloupe", 16.1700, -61.7900, "marine_park",
             "Jacques Cousteau reserve with reef and turtles in clear protected water."),
        ],
    ),
    "tobago": (
        "Trinidad and Tobago",
        "America/Port_of_Spain",
        [
            ("Buccoo Reef", "Tobago", 11.1700, -60.8500, "reef",
             "Protected reef and the Nylon Pool's clear shallow lagoon."),
        ],
    ),
    "usa": (
        "USA",
        "America/New_York",
        [
            ("Looe Key", "Florida", 24.5460, -81.4040, "reef",
             "Florida Keys sanctuary reef with spur-and-groove coral in clear water."),
            ("Bahia Honda", "Florida", 24.6550, -81.2780, "beach",
             "State-park beach with seagrass flats and nearby reef in the lower Keys."),
        ],
    ),
    "portugal-algarve": (
        "Portugal",
        "Europe/Lisbon",
        [
            ("Lagos", "Algarve", 37.1000, -8.6700, "cove",
             "Algarve cliffs and grottoes with clear Atlantic coves around Ponta da Piedade."),
        ],
    ),
    "reunion": (
        "Réunion",
        "Indian/Reunion",
        [
            ("Hermitage Lagoon", "Réunion", -21.0800, 55.2200, "reef",
             "Protected west-coast lagoon with shallow coral and reef fish."),
        ],
    ),
    "madagascar": (
        "Madagascar",
        "Indian/Antananarivo",
        [
            ("Nosy Be", "Diana", -13.3200, 48.2600, "reef",
             "Northwest island with reef, turtles and seasonal whale sharks in clear water."),
        ],
    ),
    "kenya": (
        "Kenya",
        "Africa/Nairobi",
        [
            ("Watamu", "Kilifi", -3.3560, 40.0260, "marine_park",
             "Marine national park with shallow coral gardens and turtles."),
        ],
    ),
    "mozambique": (
        "Mozambique",
        "Africa/Maputo",
        [
            ("Tofo", "Inhambane", -23.8500, 35.5450, "reef",
             "Indian Ocean beach town known for manta rays and whale sharks."),
        ],
    ),
}


def iter_spots_2():
    for country_slug, (country_name, timezone, spots) in WORLD_SPOTS_2.items():
        for spot in spots:
            yield country_slug, country_name, timezone, spot
