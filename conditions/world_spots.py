"""Curated worldwide snorkeling destinations.

A large, hand-curated list of real, well-known snorkeling spots used to expand
SnorkelForecast's indexable page footprint. Each entry becomes a SnorkelLocation
(and therefore a forecast page + sitemap entry) via the populate_world_spots
management command.

Design notes:
- Spots are spread across many countries on purpose. Country directory pages
  fetch live conditions for every city in that country, so keeping each country
  modest (rather than one giant country) limits the per-page request burst.
- Coordinates target the coastal water at each spot; the marine API snaps to the
  nearest ocean grid cell, so spot-level accuracy to ~0.1° is sufficient.
- Timezones are IANA identifiers and matter for the daylight scoring logic.
- Descriptions are specific per spot so pages are not thin/duplicate content.

Tuple format: (name, region, latitude, longitude, location_type, description)
"""

# country -> (display_country, iana_timezone, [spots])
WORLD_SPOTS: dict[str, tuple[str, str, list]] = {
    "egypt": (
        "Egypt",
        "Africa/Cairo",
        [
            ("Sharm El Sheikh", "South Sinai", 27.9158, 34.3300, "reef",
             "Red Sea resort town fringed by Ras Mohammed's world-class coral walls and reef fish."),
            ("Dahab Blue Hole", "South Sinai", 28.5721, 34.5377, "dive_site",
             "Famous Red Sea sinkhole with a shallow reef rim that is superb for snorkeling from shore."),
            ("Hurghada", "Red Sea Governorate", 27.2579, 33.8116, "reef",
             "Gateway to Giftun Island's reefs and turquoise lagoons on Egypt's Red Sea coast."),
            ("Marsa Alam", "Red Sea Governorate", 25.0676, 34.8900, "reef",
             "Quiet Red Sea coast known for dugongs, turtles and house reefs straight off the beach."),
        ],
    ),
    "maldives": (
        "Maldives",
        "Indian/Maldives",
        [
            ("Maafushi", "Kaafu Atoll", 3.9419, 73.4905, "reef",
             "Local island in South Malé Atoll ringed by house reefs, turtles and manta cleaning stations."),
            ("Hulhumalé", "Kaafu Atoll", 4.2167, 73.5400, "reef",
             "Reclaimed island near Malé with easy reef access and clear lagoon water."),
            ("Fulidhoo", "Vaavu Atoll", 3.6736, 73.4136, "reef",
             "Tiny Vaavu Atoll island famous for nurse sharks, stingrays and vibrant reef."),
        ],
    ),
    "australia": (
        "Australia",
        "Australia/Brisbane",
        [
            ("Ningaloo Reef", "Western Australia", -22.6500, 113.6500, "reef",
             "UNESCO fringing reef off Exmouth where you can snorkel with whale sharks and manta rays."),
            ("Lady Elliot Island", "Queensland", -24.1130, 152.7150, "reef",
             "Southern Great Barrier Reef coral cay renowned for manta rays and turtles."),
            ("Heron Island", "Queensland", -23.4423, 151.9148, "reef",
             "Coral cay sitting right on the Great Barrier Reef with reef accessible from the beach."),
            ("Lord Howe Island", "New South Wales", -31.5553, 159.0821, "reef",
             "World's southernmost coral reef, a clear-water lagoon with endemic fish."),
            ("Rottnest Island", "Western Australia", -32.0067, 115.5167, "bay",
             "Island off Perth with sheltered bays, seagrass meadows and shipwreck snorkel trails."),
        ],
    ),
    "indonesia": (
        "Indonesia",
        "Asia/Makassar",
        [
            ("Nusa Penida", "Bali", -8.7275, 115.5444, "reef",
             "Bali island famous for manta rays at Manta Point and dramatic Crystal Bay drop-offs."),
            ("Amed", "Bali", -8.3370, 115.6877, "reef",
             "Black-sand Bali village with calm coral gardens and the Japanese shipwreck snorkel."),
            ("Gili Trawangan", "West Nusa Tenggara", -8.3500, 116.0400, "reef",
             "Car-free island off Lombok with turtle-filled reefs and underwater statues."),
            ("Menjangan Island", "Bali", -8.0939, 114.5106, "reef",
             "West Bali Marine Park island with pristine coral walls and superb visibility."),
            ("Raja Ampat", "West Papua", -0.2346, 130.5070, "reef",
             "The planet's richest marine biodiversity, with electric coral reefs in clear shallow water."),
            ("Bunaken", "North Sulawesi", 1.6206, 124.7600, "reef",
             "Marine park island near Manado famous for vertical coral walls teeming with fish."),
        ],
    ),
    "philippines": (
        "Philippines",
        "Asia/Manila",
        [
            ("Moalboal", "Cebu", 9.9496, 123.3186, "reef",
             "Cebu town with a sardine run you can snorkel from shore plus turtles at Pescador Island."),
            ("El Nido", "Palawan", 11.1956, 119.4127, "bay",
             "Palawan lagoons and limestone cliffs surrounding clear, fish-filled bays."),
            ("Apo Island", "Negros Oriental", 9.0744, 123.2700, "reef",
             "Community marine sanctuary with healthy coral and resident sea turtles."),
            ("Panglao", "Bohol", 9.5783, 123.7600, "reef",
             "Bohol island with Balicasag's reef walls and abundant turtles and jackfish."),
            ("Coron", "Palawan", 11.9983, 120.2040, "dive_site",
             "Calauit and Coron bays with shallow reefs and famous WWII shipwrecks."),
        ],
    ),
    "thailand": (
        "Thailand",
        "Asia/Bangkok",
        [
            ("Koh Tao", "Surat Thani", 10.0956, 99.8403, "reef",
             "Gulf of Thailand island with shallow coral bays and resident green turtles."),
            ("Similan Islands", "Phang Nga", 8.6500, 97.6450, "reef",
             "Andaman archipelago marine park with granite boulders and crystal-clear reefs."),
            ("Koh Phi Phi", "Krabi", 7.7407, 98.7784, "bay",
             "Limestone islands with sheltered bays, reef sharks and bright soft coral."),
            ("Koh Lipe", "Satun", 6.4889, 99.3050, "reef",
             "Tarutao marine park island ringed by clear water and easy fringing reefs."),
            ("Surin Islands", "Phang Nga", 9.4167, 97.8667, "reef",
             "Remote Andaman islands with some of Thailand's best shallow coral gardens."),
        ],
    ),
    "mexico": (
        "Mexico",
        "America/Cancun",
        [
            ("Cozumel", "Quintana Roo", 20.4230, -86.9223, "reef",
             "Caribbean island on the Mesoamerican Reef with drift snorkeling over coral gardens."),
            ("Akumal", "Quintana Roo", 20.3947, -87.3150, "bay",
             "Sheltered Riviera Maya bay where green turtles graze on seagrass close to shore."),
            ("Isla Mujeres", "Quintana Roo", 21.2311, -86.7310, "reef",
             "Island off Cancún with the MUSA underwater museum and summer whale sharks."),
            ("Cabo Pulmo", "Baja California Sur", 23.4419, -109.4280, "reef",
             "Sea of Cortez marine park with the Gulf's only living coral reef and huge fish schools."),
            ("Tulum", "Quintana Roo", 20.2114, -87.4654, "cove",
             "Riviera Maya beaches and nearby cenotes offering reef and freshwater snorkeling."),
        ],
    ),
    "belize": (
        "Belize",
        "America/Belize",
        [
            ("Hol Chan", "Belize District", 17.8650, -87.9750, "marine_park",
             "Marine reserve cut through the barrier reef, packed with rays, sharks and reef fish."),
            ("Caye Caulker", "Belize District", 17.7400, -88.0250, "reef",
             "Laid-back caye beside the Belize Barrier Reef with Shark Ray Alley nearby."),
        ],
    ),
    "honduras": (
        "Honduras",
        "America/Tegucigalpa",
        [
            ("Roatán", "Bay Islands", 16.3000, -86.5300, "reef",
             "Bay Island on the Mesoamerican Reef with shallow coral walls off many beaches."),
            ("Utila", "Bay Islands", 16.1000, -86.9000, "reef",
             "Budget dive island with whale sharks and easy reef snorkeling from shore."),
        ],
    ),
    "bahamas": (
        "Bahamas",
        "America/Nassau",
        [
            ("Nassau", "New Providence", 25.0780, -77.3380, "reef",
             "Capital island with shallow reefs, blue holes and clear turquoise shallows."),
            ("Exuma", "Exuma", 23.6200, -75.9800, "cove",
             "Island chain known for swimming pigs, Thunderball Grotto and bright sandbanks."),
        ],
    ),
    "cayman-islands": (
        "Cayman Islands",
        "America/Cayman",
        [
            ("Grand Cayman", "Grand Cayman", 19.3580, -81.2546, "reef",
             "Home to Stingray City and the shallow coral gardens of the North Sound."),
            ("Little Cayman", "Little Cayman", 19.6890, -80.0700, "reef",
             "Tiny island fringed by Bloody Bay Wall and pristine, fish-rich shallows."),
        ],
    ),
    "bonaire": (
        "Bonaire",
        "America/Kralendijk",
        [
            ("Kralendijk", "Bonaire", 12.1500, -68.2767, "reef",
             "Shore-diving capital whose entire leeward coast is a protected fringing reef."),
            ("Klein Bonaire", "Bonaire", 12.1620, -68.3060, "reef",
             "Uninhabited islet with shallow coral and turtles a short boat hop from town."),
        ],
    ),
    "curacao": (
        "Curaçao",
        "America/Curacao",
        [
            ("Playa Lagun", "Curaçao", 12.3200, -69.1500, "cove",
             "Sheltered cove famous for turtles feeding close to the small beach."),
            ("Tugboat Beach", "Curaçao", 12.0820, -68.8600, "reef",
             "Calm bay with a shallow sunken tugboat wreck blanketed in coral."),
        ],
    ),
    "usvi": (
        "US Virgin Islands",
        "America/St_Thomas",
        [
            ("Trunk Bay", "St. John", 18.3550, -64.7700, "bay",
             "Virgin Islands National Park bay with a marked underwater snorkeling trail."),
            ("Buck Island", "St. Croix", 17.7900, -64.6200, "reef",
             "National monument with an underwater trail through an elkhorn coral barrier reef."),
        ],
    ),
    "puerto-rico": (
        "Puerto Rico",
        "America/Puerto_Rico",
        [
            ("Culebra", "Culebra", 18.3050, -65.3010, "reef",
             "Island east of the mainland with Flamenco Beach and calm reef-lined bays."),
            ("La Parguera", "Lajas", 17.9730, -67.0460, "reef",
             "Southwest coast mangrove channels, reefs and a bioluminescent bay."),
        ],
    ),
    "usa": (
        "USA",
        "America/New_York",
        [
            ("Key Largo", "Florida", 25.0865, -80.4473, "reef",
             "Gateway to John Pennekamp park and the shallow Florida Keys reef tract."),
            ("Dry Tortugas", "Florida", 24.6285, -82.8732, "reef",
             "Remote Gulf islands with coral, seagrass and historic Fort Jefferson's moat wall."),
            ("La Jolla Cove", "California", 32.8500, -117.2710, "cove",
             "San Diego marine reserve with garibaldi, leopard sharks and a kelp forest."),
            ("Catalina Island", "California", 33.3879, -118.4163, "cove",
             "Lover's Cove and Casino Point reserve offer clear-water kelp snorkeling off LA."),
            ("Crystal River", "Florida", 28.9025, -82.5926, "other",
             "Spring-fed Gulf coast river where you can snorkel alongside wintering manatees."),
        ],
    ),
    "spain": (
        "Spain",
        "Atlantic/Canary",
        [
            ("Tenerife", "Canary Islands", 28.2916, -16.6291, "reef",
             "Canary island with volcanic reefs, turtles at El Puertito and warm Atlantic water."),
            ("Lanzarote", "Canary Islands", 28.9630, -13.5477, "reef",
             "Volcanic Canary island with Playa Chica's clear water and the Museo Atlántico statues."),
            ("Fuerteventura", "Canary Islands", 28.3587, -14.0537, "beach",
             "Canary island with calm lagoons at Caleta de Fuste and turquoise shallows."),
        ],
    ),
    "spain-mediterranean": (
        "Spain",
        "Europe/Madrid",
        [
            ("Mallorca", "Balearic Islands", 39.5696, 2.6502, "cove",
             "Balearic island laced with sheltered calas of crystal-clear Mediterranean water."),
            ("Menorca", "Balearic Islands", 39.9496, 4.1100, "cove",
             "Quietest Balearic, ringed by turquoise coves and protected reserves."),
            ("Cabo de Gata", "Andalusia", 36.7300, -2.1900, "marine_park",
             "Volcanic Andalusian marine park with seagrass meadows and clear coves."),
        ],
    ),
    "greece": (
        "Greece",
        "Europe/Athens",
        [
            ("Milos", "Cyclades", 36.7400, 24.4200, "cove",
             "Volcanic Cycladic island with Sarakiniko's white rocks and clear swimming coves."),
            ("Paros", "Cyclades", 37.0855, 25.1490, "bay",
             "Cycladic island with sheltered bays and bright Aegean shallows."),
            ("Rhodes", "Dodecanese", 36.1700, 28.0000, "bay",
             "Dodecanese island whose Anthony Quinn Bay is a famous rocky snorkeling cove."),
            ("Kefalonia", "Ionian Islands", 38.1750, 20.5600, "cove",
             "Ionian island with the turquoise water of Myrtos and sheltered pebble coves."),
            ("Crete", "Crete", 35.2401, 24.8093, "coastline",
             "Largest Greek island with clear coves, caves and warm Libyan Sea shallows."),
        ],
    ),
    "italy": (
        "Italy",
        "Europe/Rome",
        [
            ("Sardinia", "Sardinia", 41.1170, 9.5150, "cove",
             "Mediterranean island ringed by white sand and the clear coves of the Maddalena."),
            ("Taormina", "Sicily", 37.8520, 15.2930, "bay",
             "Sicilian coast with Isola Bella's pebble bay and clear rocky shallows."),
            ("Ustica", "Sicily", 38.7060, 13.1900, "marine_park",
             "Volcanic island marine reserve north of Palermo with vivid clear water."),
            ("Elba", "Tuscany", 42.7780, 10.2370, "cove",
             "Tuscan archipelago island with sheltered coves and seagrass-clear water."),
        ],
    ),
    "croatia": (
        "Croatia",
        "Europe/Zagreb",
        [
            ("Vis", "Split-Dalmatia", 43.0617, 16.1817, "cove",
             "Remote Adriatic island with the Blue Cave nearby and exceptionally clear coves."),
            ("Brač", "Split-Dalmatia", 43.3140, 16.6500, "beach",
             "Island home to Zlatni Rat beach and clear pebbly Adriatic shallows."),
            ("Mljet", "Dubrovnik-Neretva", 42.7500, 17.5300, "marine_park",
             "Forested national-park island with saltwater lakes and clear sheltered bays."),
            ("Rovinj", "Istria", 45.0810, 13.6387, "coastline",
             "Istrian town with rocky coves and clear northern Adriatic water."),
        ],
    ),
    "france": (
        "France",
        "Europe/Paris",
        [
            ("Calanques de Marseille", "Provence", 43.2100, 5.4400, "cove",
             "Limestone fjords near Marseille with clear, sheltered Mediterranean coves."),
            ("Cap d'Antibes", "Côte d'Azur", 43.5500, 7.1200, "coastline",
             "Riviera headland with rocky snorkeling trails and clear blue water."),
            ("Corsica", "Corsica", 41.9200, 8.7400, "cove",
             "Mediterranean island with the Scandola reserve and turquoise granite coves."),
        ],
    ),
    "portugal": (
        "Portugal",
        "Atlantic/Azores",
        [
            ("Azores - São Miguel", "Azores", 37.7400, -25.6800, "dive_site",
             "Mid-Atlantic volcanic island with clear water, islets and even snorkeling with blue sharks offshore."),
            ("Azores - Pico", "Azores", 38.4600, -28.3300, "dive_site",
             "Volcanic island with dramatic underwater landscapes and clear ocean water."),
        ],
    ),
    "portugal-madeira": (
        "Portugal",
        "Atlantic/Madeira",
        [
            ("Madeira - Garajau", "Madeira", 32.6400, -16.8500, "marine_park",
             "Atlantic marine reserve where dusky groupers approach snorkelers in clear water."),
            ("Porto Santo", "Madeira", 33.0700, -16.3400, "beach",
             "Golden-sand island near Madeira with calm, clear Atlantic shallows."),
        ],
    ),
    "turkey": (
        "Turkey",
        "Europe/Istanbul",
        [
            ("Fethiye", "Muğla", 36.6200, 29.1200, "bay",
             "Turquoise Coast hub with Ölüdeniz lagoon and sheltered clear bays."),
            ("Kalkan", "Antalya", 36.2650, 29.4130, "bay",
             "Lycian coast town with deep-blue clear water and rocky snorkeling coves."),
            ("Marmaris", "Muğla", 36.8550, 28.2740, "bay",
             "Aegean-Med resort with sheltered bays and clear water around Turunç."),
        ],
    ),
    "costa-rica": (
        "Costa Rica",
        "America/Costa_Rica",
        [
            ("Caño Island", "Puntarenas", 8.7150, -83.8800, "reef",
             "Pacific biological reserve with rays, reef fish and clear protected water."),
            ("Manuel Antonio", "Puntarenas", 9.3900, -84.1500, "bay",
             "National-park beaches with calm bays and reef close to shore."),
        ],
    ),
    "panama": (
        "Panama",
        "America/Panama",
        [
            ("Bocas del Toro", "Bocas del Toro", 9.3400, -82.2400, "reef",
             "Caribbean archipelago with mangrove channels, starfish beaches and coral cays."),
            ("San Blas Islands", "Guna Yala", 9.5700, -78.8200, "reef",
             "Guna Yala palm islets with shallow reefs and shipwrecks in clear water."),
        ],
    ),
    "colombia": (
        "Colombia",
        "America/Bogota",
        [
            ("San Andrés", "San Andrés", 12.5840, -81.7000, "reef",
             "Caribbean island in a sea of seven colors with shallow reefs and cays."),
            ("Providencia", "San Andrés", 13.3500, -81.3700, "reef",
             "Remote island backed by the third-largest barrier reef in the world."),
        ],
    ),
    "brazil": (
        "Brazil",
        "America/Noronha",
        [
            ("Fernando de Noronha", "Pernambuco", -3.8540, -32.4250, "marine_park",
             "Atlantic archipelago marine park with turtles, reef sharks and clear natural pools."),
        ],
    ),
    "ecuador": (
        "Ecuador",
        "Pacific/Galapagos",
        [
            ("Santa Cruz", "Galápagos", -0.7440, -90.3130, "reef",
             "Galápagos hub with sea lions, turtles and rays at Las Grietas and Tortuga Bay."),
            ("San Cristóbal", "Galápagos", -0.9020, -89.6100, "reef",
             "Galápagos island where sea lions and reef fish fill the shallow Kicker Rock bays."),
            ("Isabela", "Galápagos", -0.9620, -90.9600, "reef",
             "Largest Galápagos island with penguins, turtles and sharks in clear lagoons."),
        ],
    ),
    "seychelles": (
        "Seychelles",
        "Indian/Mahe",
        [
            ("Mahé", "Mahé", -4.6796, 55.4920, "reef",
             "Main granite island with Ste Anne Marine Park and clear reef-fringed bays."),
            ("Praslin", "Praslin", -4.3180, 55.7380, "reef",
             "Granite island with St Pierre islet's coral and warm clear Indian Ocean water."),
            ("La Digue", "La Digue", -4.3590, 55.8390, "reef",
             "Iconic granite-boulder beaches with calm, clear snorkeling shallows."),
        ],
    ),
    "mauritius": (
        "Mauritius",
        "Indian/Mauritius",
        [
            ("Blue Bay", "Grand Port", -20.4430, 57.7100, "marine_park",
             "Marine park lagoon with shallow coral and brilliant clear turquoise water."),
            ("Flic en Flac", "Black River", -20.2740, 57.3630, "reef",
             "West-coast lagoon with calm reef shallows and frequent turtles and dolphins."),
        ],
    ),
    "tanzania": (
        "Tanzania",
        "Africa/Dar_es_Salaam",
        [
            ("Mnemba Atoll", "Zanzibar", -5.8170, 39.3870, "reef",
             "Zanzibar atoll with a protected reef, turtles and dolphins in clear water."),
            ("Mafia Island", "Mafia", -7.9200, 39.7700, "reef",
             "Marine-park island with whale sharks and pristine reef south of Zanzibar."),
        ],
    ),
    "fiji": (
        "Fiji",
        "Pacific/Fiji",
        [
            ("Mamanuca Islands", "Western", -17.6700, 177.1000, "reef",
             "Resort islands ringed by shallow coral and clear lagoon shallows."),
            ("Taveuni", "Cakaudrove", -16.8500, -179.9700, "reef",
             "The Garden Island beside the Rainbow Reef's famous soft corals."),
        ],
    ),
    "french-polynesia": (
        "French Polynesia",
        "Pacific/Tahiti",
        [
            ("Moorea", "Society Islands", -17.5388, -149.8295, "reef",
             "Lagoon island where rays and blacktip sharks glide over clear coral gardens."),
            ("Bora Bora", "Society Islands", -16.5004, -151.7415, "reef",
             "Iconic lagoon with coral gardens, rays and warm crystal-clear water."),
            ("Rangiroa", "Tuamotus", -15.1200, -147.6400, "reef",
             "Vast atoll with drift snorkeling through passes full of sharks and fish."),
        ],
    ),
    "japan": (
        "Japan",
        "Asia/Tokyo",
        [
            ("Kerama Islands", "Okinawa", 26.1900, 127.3500, "reef",
             "Okinawan islands with 'Kerama blue' water, turtles and bright coral."),
            ("Ishigaki", "Okinawa", 24.3400, 124.1600, "reef",
             "Yaeyama island with manta rays at Kabira and clear subtropical reefs."),
            ("Miyako", "Okinawa", 24.7900, 125.3100, "reef",
             "Okinawan island ringed by white sand and clear coral shallows."),
        ],
    ),
    "sri-lanka": (
        "Sri Lanka",
        "Asia/Colombo",
        [
            ("Pigeon Island", "Trincomalee", 8.7160, 81.2070, "reef",
             "National-park island off Trincomalee with reef sharks and shallow coral."),
            ("Hikkaduwa", "Southern Province", 6.1390, 80.0990, "reef",
             "South-coast reef sanctuary with turtles in calm shallow water."),
        ],
    ),
    "malaysia": (
        "Malaysia",
        "Asia/Kuala_Lumpur",
        [
            ("Perhentian Islands", "Terengganu", 5.9100, 102.7300, "reef",
             "Clear-water islands with turtles, reef sharks and coral off the beaches."),
            ("Tioman Island", "Pahang", 2.7900, 104.1700, "reef",
             "Forested South China Sea island with coral bays and easy reef access."),
            ("Redang Island", "Terengganu", 5.7800, 103.0100, "reef",
             "Marine-park island with powdery sand and shallow coral full of fish."),
            ("Sipadan", "Sabah", 4.1150, 118.6290, "reef",
             "Oceanic island off Borneo famous for turtles and walls of barracuda."),
        ],
    ),
    "vietnam": (
        "Vietnam",
        "Asia/Ho_Chi_Minh",
        [
            ("Nha Trang", "Khánh Hòa", 12.2388, 109.1967, "reef",
             "Bay city with Hon Mun marine reserve and shallow reef islands offshore."),
            ("Phú Quốc", "Kiên Giang", 10.2270, 103.9670, "reef",
             "Gulf of Thailand island with An Thoi archipelago coral and clear shallows."),
        ],
    ),
    "jordan": (
        "Jordan",
        "Asia/Amman",
        [
            ("Aqaba", "Aqaba", 29.4470, 34.9970, "reef",
             "Jordan's Red Sea coast with shore reefs, coral and the Cedar Pride wreck."),
        ],
    ),
    "israel": (
        "Israel",
        "Asia/Jerusalem",
        [
            ("Eilat", "Southern District", 29.5030, 34.9180, "reef",
             "Red Sea resort with a protected coral-reserve reef snorkelable from the beach."),
        ],
    ),
    "oman": (
        "Oman",
        "Asia/Muscat",
        [
            ("Daymaniyat Islands", "Al Batinah", 23.8500, 58.0900, "reef",
             "Protected island reserve off Muscat with turtles, rays and clear reef water."),
        ],
    ),
    "new-zealand": (
        "New Zealand",
        "Pacific/Auckland",
        [
            ("Goat Island", "Auckland", -36.2680, 174.7990, "marine_park",
             "New Zealand's first marine reserve, with snapper and kelp in clear shallows."),
            ("Poor Knights Islands", "Northland", -35.4670, 174.7360, "dive_site",
             "Subtropical reserve islands rated among the world's best for clear-water snorkeling."),
        ],
    ),
    "south-africa": (
        "South Africa",
        "Africa/Johannesburg",
        [
            ("Sodwana Bay", "KwaZulu-Natal", -27.5400, 32.6800, "reef",
             "South Africa's premier coral reefs with warm Indian Ocean shallows."),
        ],
    ),
    "grenada": (
        "Grenada",
        "America/Grenada",
        [
            ("Molinere Bay", "St. George", 12.0900, -61.7600, "marine_park",
             "Home to the Caribbean's underwater sculpture park in shallow clear water."),
        ],
    ),
    "antigua-and-barbuda": (
        "Antigua and Barbuda",
        "America/Antigua",
        [
            ("Cades Reef", "Antigua", 17.0200, -61.8900, "reef",
             "Long sheltered barrier reef off Antigua's southwest coast with calm shallows."),
        ],
    ),
    "saint-lucia": (
        "Saint Lucia",
        "America/St_Lucia",
        [
            ("Anse Chastanet", "Soufrière", 13.8640, -61.0840, "reef",
             "Marine-reserve reef beneath the Pitons, snorkelable straight off the beach."),
        ],
    ),
    "barbados": (
        "Barbados",
        "America/Barbados",
        [
            ("Carlisle Bay", "St. Michael", 13.0780, -59.6130, "bay",
             "Calm west-coast bay with turtles and shallow shipwrecks close to shore."),
        ],
    ),
}


def iter_spots():
    """Yield (country_slug, country_name, timezone, spot_tuple) for every spot.

    Includes both the primary batch (this module) and the second batch in
    conditions/world_spots_2.py.
    """
    for country_slug, (country_name, timezone, spots) in WORLD_SPOTS.items():
        for spot in spots:
            yield country_slug, country_name, timezone, spot

    try:
        from .world_spots_2 import iter_spots_2
    except ImportError:
        return
    yield from iter_spots_2()
