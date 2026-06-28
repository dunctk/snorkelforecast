"""Evergreen snorkeling guides.

These cornerstone articles target informational queries that Search Console
shows SnorkelForecast already receives impressions for but had no matching
page to answer (e.g. "best tide for snorkeling", "best time to snorkel",
"snorkeling water temperature", "how deep is snorkeling water").

Content is stored here (not the DB) so guides are version-controlled and
require no migrations. Each guide renders through conditions/templates/
conditions/guide_detail.html.
"""

from copy import deepcopy

from django.utils import translation
from django.utils.safestring import mark_safe

GUIDES = [
    {
        "slug": "best-time-to-snorkel",
        "title": "Best Time to Snorkel: Tide, Time of Day and Season",
        "summary": (
            "The best time to snorkel is a calm morning around high tide, in a "
            "season when the water is warm and the sea is settled. Here's how each "
            "factor affects visibility and safety."
        ),
        "faqs": [
            {
                "q": "What is the best tide for snorkeling?",
                "a": (
                    "High tide is usually best. Within roughly an hour of the high-tide "
                    "peak the water is deepest over the reef and currents are weakest "
                    "(slack water), which means better visibility and easier, safer "
                    "swimming. Strong incoming or outgoing tides create currents that stir "
                    "up sand and sediment and can pull you off your line."
                ),
            },
            {
                "q": "What time of day is best for snorkeling?",
                "a": (
                    "Early to mid-morning. Wind and waves typically build through the "
                    "afternoon as the land heats up, so mornings are usually the calmest "
                    "and clearest. Late morning also gives good overhead sun for light and "
                    "colour underwater."
                ),
            },
            {
                "q": "How deep is the water when you snorkel?",
                "a": (
                    "Most snorkeling happens over water 1 to 5 metres (3 to 16 feet) deep, "
                    "where you can clearly see the reef or seabed from the surface. You "
                    "float on top and look down, so you don't need to be able to touch the "
                    "bottom — but beginners often prefer shallower, calmer areas to start."
                ),
            },
        ],
        "body": mark_safe(
            """
<p>Ask any experienced snorkeler when to get in the water and you'll hear the same answer: <strong>a calm morning, around high tide</strong>. Three things decide whether a snorkel session is great or disappointing — the tide, the time of day, and the season. Here's how each one works, and how to use a forecast to line them up.</p>

<h2>Tide: aim for the window around high tide</h2>
<p>The best snorkeling is usually within about an hour of high tide. At the top of the tide the water is at its deepest over the reef, and the flow between tides is at its weakest — a period called <em>slack water</em>. Weak currents mean clearer water (less stirred-up sediment) and easier, safer swimming. Avoid the middle of a big incoming or outgoing tide, when currents are strongest.</p>

<h2>Time of day: mornings are calmest</h2>
<p>Wind almost always builds through the day as the land heats up and sea breezes develop. Calmer wind means smaller waves, a flatter surface and better visibility, so the early-to-mid morning is typically the best window. As a bonus, the higher the sun, the more light and colour you'll see underwater.</p>

<h2>Season: warm water and settled weather</h2>
<p>The right season depends on your destination, but you're looking for warm water (most snorkelers are comfortable from about 20–30&deg;C / 68–86&deg;F) and a settled-weather period without big swells. Many destinations have a clear "best months" window — for example, summer mornings in the Mediterranean, or the calmer summer season on Hawaii's exposed north shores.</p>

<h2>Put it together with a live forecast</h2>
<p>You don't have to guess. A snorkeling forecast scores each daylight hour using wave height, wind speed, water temperature, tide and current, so you can pick the exact window where everything lines up. Browse your destination below to see today's best snorkel window and the best months to visit.</p>
"""
        ),
    },
    {
        "slug": "snorkeling-water-temperature",
        "title": "What Water Temperature Is Good for Snorkeling?",
        "summary": (
            "Most people snorkel comfortably in water between 20 and 30°C "
            "(68–86°F). Below that, a wetsuit or rash guard makes a big "
            "difference. Here's a simple temperature guide plus what to wear."
        ),
        "faqs": [
            {
                "q": "What water temperature is comfortable for snorkeling?",
                "a": (
                    "Most snorkelers are comfortable between 20 and 30°C (68 to 86°F). "
                    "Around 25–28°C is ideal for swimwear alone. From 18 to 22°C a "
                    "rash guard or shorty wetsuit helps, and below about 18°C you'll want "
                    "a 3mm or thicker wetsuit to stay warm."
                ),
            },
            {
                "q": "Is 20°C water too cold to snorkel?",
                "a": (
                    "20°C (68°F) is on the cool side but fine for a shorter snorkel, "
                    "especially with a rash guard or shorty wetsuit. You lose heat far "
                    "faster in water than in air, so if you start shivering, get out and "
                    "warm up."
                ),
            },
            {
                "q": "How can I check the water temperature before I go?",
                "a": (
                    "Use a sea-surface-temperature forecast for your exact spot. "
                    "SnorkelForecast shows the current and recent average sea temperature "
                    "for each location, along with wave, wind and tide conditions."
                ),
            },
        ],
        "body": mark_safe(
            """
<p>Water temperature makes or breaks a snorkel. You lose body heat roughly 25 times faster in water than in air, so a sea that feels "fine" for a quick dip can get cold surprisingly quickly when you're floating still and looking down. Here's a simple guide to what's comfortable, and what to wear.</p>

<h2>A simple temperature guide</h2>
<ul>
  <li><strong>28–30&deg;C (82–86&deg;F)</strong> — bath-warm tropical water; swimwear only, snorkel as long as you like.</li>
  <li><strong>25–28&deg;C (77–82&deg;F)</strong> — ideal for most people in swimwear.</li>
  <li><strong>22–25&deg;C (72–77&deg;F)</strong> — comfortable for most; a rash guard adds a little warmth and sun protection.</li>
  <li><strong>18–22&deg;C (64–72&deg;F)</strong> — cool; a shorty or 3mm wetsuit keeps you in longer.</li>
  <li><strong>Below 18&deg;C (64&deg;F)</strong> — cold; wear a 3mm+ wetsuit and keep sessions short.</li>
</ul>

<h2>What to wear</h2>
<p>A <strong>rash guard</strong> blocks sun and takes the edge off cool water. A <strong>shorty wetsuit</strong> (short arms and legs) suits 20–24&deg;C. A <strong>full 3mm wetsuit</strong> is the go-to below about 20&deg;C, and warmer still with a 5mm in cooler seas. Even in warm water, a thin top helps prevent sunburn on your back — the part of you that's exposed the whole time.</p>

<h2>Why the forecast matters</h2>
<p>Sea temperature varies a lot by location and season, and changes through the year. Rather than rely on averages, check the current and recent sea temperature for your specific spot before you go. Browse a destination below to see its live water temperature alongside wave, wind and tide conditions.</p>
"""
        ),
    },
    {
        "slug": "best-snorkeling-destinations",
        "title": "The Best Snorkeling Destinations in the World",
        "summary": (
            "From the Great Barrier Reef and the Maldives to Hawaii, the Red Sea "
            "and the Caribbean — a guide to the world's best places to snorkel, "
            "and how to check live conditions for each before you go."
        ),
        "faqs": [
            {
                "q": "Where is the best snorkeling in the world?",
                "a": (
                    "The most celebrated snorkeling destinations include the Great Barrier "
                    "Reef and Ningaloo Reef (Australia), the Maldives, the Red Sea (Egypt), "
                    "Hawaii, Raja Ampat (Indonesia), the Galápagos, Palau, and Caribbean "
                    "reefs like Bonaire, Cozumel and Belize. The 'best' for you depends on "
                    "season, water temperature and how calm the conditions are when you visit."
                ),
            },
            {
                "q": "What makes a great snorkeling destination?",
                "a": (
                    "Clear, warm water; sheltered bays or reefs that stay calm; abundant "
                    "marine life; and easy entry from shore or a short boat ride. The single "
                    "biggest day-to-day factor is conditions — low waves and wind, good "
                    "visibility and slack tide — which is why checking a live forecast for "
                    "your exact spot matters as much as the destination itself."
                ),
            },
        ],
        "body": mark_safe(
            """
<p>The world is full of extraordinary places to snorkel — but the difference between an unforgettable swim and a murky, choppy disappointment usually comes down to <strong>picking the right spot at the right time</strong>. Below are some of the planet's best snorkeling destinations, grouped by region, with a live forecast for each so you can see today's conditions before you go.</p>

<h2>Pacific &amp; Hawaii</h2>
<ul>
  <li><a href="/usa/maui/">Maui, Hawaii</a> — turtles and reef off easy beaches like <a href="/usa/honolua-bay/">Honolua Bay</a> and <a href="/usa/molokini-crater/">Molokini Crater</a>.</li>
  <li><a href="/usa/hanauma-bay/">Hanauma Bay, Oahu</a> — a protected volcanic-cone reef, Hawaii's most popular spot.</li>
  <li><a href="/french-polynesia/moorea/">Moorea</a> and <a href="/french-polynesia/bora-bora/">Bora Bora</a> — lagoon rays and sharks in warm, clear water.</li>
</ul>

<h2>Australia &amp; the Great Barrier Reef</h2>
<ul>
  <li><a href="/australia/ningaloo-reef/">Ningaloo Reef</a> — whale sharks and a reef metres off the beach.</li>
  <li><a href="/australia/lady-elliot-island/">Lady Elliot Island</a> and <a href="/australia/heron-island/">Heron Island</a> — coral cays on the Great Barrier Reef.</li>
</ul>

<h2>Southeast Asia</h2>
<ul>
  <li><a href="/indonesia/raja-ampat/">Raja Ampat, Indonesia</a> — the richest marine biodiversity on Earth.</li>
  <li><a href="/thailand/similan-islands/">Similan Islands, Thailand</a> and <a href="/philippines/moalboal/">Moalboal, Philippines</a> — clear reefs and a famous sardine run.</li>
</ul>

<h2>The Maldives &amp; Indian Ocean</h2>
<ul>
  <li><a href="/maldives/maafushi/">Maldives</a> — house reefs, mantas and turtles off almost every island.</li>
  <li><a href="/seychelles/mahe/">Seychelles</a> and <a href="/mauritius/blue-bay/">Mauritius</a> — granite-island reefs and lagoon shallows.</li>
</ul>

<h2>The Red Sea</h2>
<ul>
  <li><a href="/egypt/sharm-el-sheikh/">Sharm El Sheikh</a> and <a href="/egypt/dahab-blue-hole/">Dahab</a>, Egypt — coral walls and turtles straight off the shore.</li>
</ul>

<h2>The Caribbean &amp; Central America</h2>
<ul>
  <li><a href="/bonaire/kralendijk/">Bonaire</a> — a whole island fringed by a protected shore reef.</li>
  <li><a href="/mexico/cozumel/">Cozumel, Mexico</a> and <a href="/belize/hol-chan/">Hol Chan, Belize</a> — drift reefs on the Mesoamerican Reef.</li>
</ul>

<h2>The Mediterranean &amp; Atlantic</h2>
<ul>
  <li><a href="/greece/milos/">Milos, Greece</a> and <a href="/spain/medes-islands/">the Medes Islands, Spain</a> — clear coves and protected reserves.</li>
  <li><a href="/iceland/silfra/">Silfra, Iceland</a> — snorkel between two continents in glacier-clear water (drysuit only).</li>
</ul>

<h2>Before you go: check the conditions</h2>
<p>Wherever you choose, the same rule applies: snorkel on a calm morning around high tide, when the water is clearest and currents are weakest. Open any destination above to see its live snorkel score for the next 72 hours, the next good window, and the best months to visit. Or <a href="/countries/">browse all 80+ countries</a> to find a spot near you.</p>
"""
        ),
    },
    {
        "slug": "best-snorkeling-in-greece",
        "title": "Best Snorkeling in Greece: Top Islands & Spots",
        "summary": (
            "Greece's clear, calm Aegean and Ionian waters make it one of Europe's "
            "best snorkeling destinations. Here are the top islands and spots, plus "
            "how to check live conditions before you go."
        ),
        "faqs": [
            {
                "q": "Where is the best snorkeling in Greece?",
                "a": (
                    "Some of the best snorkeling in Greece is around the Ionian islands "
                    "(Zakynthos, Kefalonia, Lefkada, Corfu) and the Cyclades (Milos, Paros, "
                    "Naxos), plus Rhodes' Anthony Quinn Bay in the Dodecanese. These offer "
                    "clear, sheltered coves with rocky reefs and good visibility."
                ),
            },
            {
                "q": "When is the best time to snorkel in Greece?",
                "a": (
                    "June to September, when the sea is warmest (around 24–26°C) and "
                    "calmest. Snorkel in the morning before the afternoon meltemi wind picks "
                    "up, especially in the Cyclades."
                ),
            },
        ],
        "body": mark_safe(
            """
<p>With warm, clear water and thousands of sheltered coves, <strong>Greece is one of the best snorkeling destinations in Europe</strong>. Visibility is excellent across the Ionian and Aegean seas, and most spots are calm rocky coves ideal for spotting fish, octopus and the occasional sea turtle. Here are the top islands and spots, each with a live forecast.</p>

<h2>Ionian Islands (west)</h2>
<ul>
  <li><a href="/greece/zakynthos/">Zakynthos</a> — clear Ionian water, plus the famous <a href="/greece/zakynthos-navagio/">Navagio (Shipwreck) cove</a> and Blue Caves.</li>
  <li><a href="/greece/kefalonia/">Kefalonia</a> — turquoise bays and sheltered pebble coves.</li>
  <li><a href="/greece/lefkada/">Lefkada</a> — Porto Katsiki and bright, calm swimming bays.</li>
  <li><a href="/greece/corfu/">Corfu</a> — green island with rocky reefs and clear shallows.</li>
</ul>

<h2>Cyclades (central Aegean)</h2>
<ul>
  <li><a href="/greece/milos/">Milos</a> — volcanic rock formations and clear coves like Sarakiniko.</li>
  <li><a href="/greece/paros/">Paros</a> and <a href="/greece/naxos/">Naxos</a> — sheltered sandy bays and bright shallows.</li>
  <li><a href="/greece/santorini/">Santorini</a> — volcanic underwater landscapes and warm water.</li>
</ul>

<h2>Dodecanese &amp; Crete</h2>
<ul>
  <li><a href="/greece/rhodes/">Rhodes</a> — Anthony Quinn Bay is a classic rocky snorkeling cove.</li>
  <li><a href="/greece/kos/">Kos</a> and <a href="/greece/symi/">Symi</a> — calm bays and deep, clear coves.</li>
  <li><a href="/greece/crete/">Crete</a> — clear coves, caves and warm Libyan Sea shallows.</li>
</ul>

<h2>Plan around the conditions</h2>
<p>Greek summers are reliably calm, but the afternoon <em>meltemi</em> wind can stir up the Cyclades — so snorkel in the morning, around high tide, for the clearest water. Open any island above to see its live snorkel score and the best window over the next 72 hours. You can also <a href="/greece/">browse every Greek spot we forecast</a>.</p>
"""
        ),
    },
    {
        "slug": "best-snorkeling-in-hawaii",
        "title": "Best Snorkeling in Hawaii: Top Spots by Island",
        "summary": (
            "Hawaii has some of the world's best beginner-friendly snorkeling, with "
            "turtles, reef fish and clear water off easy-access beaches. Here are the "
            "top spots on Maui, Oahu and the Big Island, with live conditions."
        ),
        "faqs": [
            {
                "q": "What is the best snorkeling spot in Hawaii?",
                "a": (
                    "Top spots include Honolua Bay and Molokini Crater on Maui, Hanauma Bay "
                    "on Oahu, and Kealakekua Bay and Two Step on the Big Island. The best one "
                    "on any given day depends on conditions — pick the calmest, clearest spot "
                    "using a live forecast."
                ),
            },
            {
                "q": "When is the best time to snorkel in Hawaii?",
                "a": (
                    "Early morning, and generally the summer months (April–October) when "
                    "north-shore swells are smaller. Snorkel before the trade winds build and "
                    "around high tide for the clearest water."
                ),
            },
        ],
        "body": mark_safe(
            """
<p><strong>Hawaii is one of the world's best places to snorkel</strong>, with warm water, green sea turtles and reef fish accessible right from the beach. Conditions vary a lot by island, shore and season — exposed north shores can be rough in winter — so checking a live forecast for your exact spot is key. Here are the top spots by island.</p>

<h2>Maui</h2>
<ul>
  <li><a href="/usa/honolua-bay/">Honolua Bay</a> — a marine reserve with vibrant coral, best on calm summer mornings.</li>
  <li><a href="/usa/molokini-crater/">Molokini Crater</a> — a crescent volcanic crater with 30m+ visibility.</li>
  <li><a href="/usa/kaanapali-beach/">Kaanapali (Black Rock)</a>, <a href="/usa/napili-bay/">Napili Bay</a> and <a href="/usa/kapalua-bay/">Kapalua Bay</a> — easy, beginner-friendly turtle beaches.</li>
</ul>

<h2>Oahu</h2>
<ul>
  <li><a href="/usa/hanauma-bay/">Hanauma Bay</a> — a protected reef inside a volcanic cone, Hawaii's most popular spot.</li>
</ul>

<h2>Big Island</h2>
<ul>
  <li><a href="/usa/kealakekua-bay/">Kealakekua Bay</a> — a marine sanctuary with some of Hawaii's healthiest coral.</li>
  <li><a href="/usa/two-step-honaunau/">Two Step (Honaunau)</a> — easy lava-ledge entry, thriving reef and frequent dolphins.</li>
</ul>

<h2>Check before you go</h2>
<p>The golden rule in Hawaii: snorkel in the morning, around high tide, before wind and surf build — and skip exposed shores on high-surf days. Open any spot above to see today's snorkel score, the next good window and the best months. Or <a href="/usa/">see every Hawaii and US spot we forecast</a>.</p>
"""
        ),
    },
]

GUIDES_ES = [
    {
        "slug": "best-time-to-snorkel",
        "title": "Mejor hora para hacer snorkel: marea, momento del día y temporada",
        "summary": (
            "La mejor hora para hacer snorkel suele ser una mañana tranquila cerca de la "
            "pleamar, en una temporada con agua cálida y mar estable. Así influye cada "
            "factor en la visibilidad y la seguridad."
        ),
        "faqs": [
            {
                "q": "¿Cuál es la mejor marea para hacer snorkel?",
                "a": (
                    "La pleamar suele ser la mejor. Aproximadamente dentro de una hora del "
                    "pico de marea alta, el agua cubre mejor el arrecife y la corriente es "
                    "más débil, lo que mejora la visibilidad y hace que nadar sea más fácil."
                ),
            },
            {
                "q": "¿Qué hora del día es mejor para hacer snorkel?",
                "a": (
                    "De primera a media mañana. El viento y el oleaje suelen aumentar por "
                    "la tarde, así que las mañanas acostumbran a ser más tranquilas y claras."
                ),
            },
            {
                "q": "¿A qué profundidad se hace snorkel?",
                "a": (
                    "La mayoría del snorkel se hace sobre fondos de 1 a 5 metros, donde se "
                    "puede ver el arrecife o el fondo desde la superficie. No hace falta tocar "
                    "el fondo, aunque los principiantes suelen preferir zonas someras y calmadas."
                ),
            },
        ],
        "body": mark_safe(
            """
<p>Si preguntas a alguien con experiencia cuándo meterse al agua, casi siempre oirás lo mismo: <strong>una mañana calmada, cerca de la pleamar</strong>. Tres factores deciden si una salida de snorkel será buena o decepcionante: la marea, la hora del día y la temporada.</p>

<h2>Marea: busca la ventana alrededor de la pleamar</h2>
<p>El mejor snorkel suele darse aproximadamente dentro de una hora de la pleamar. En ese momento hay más profundidad sobre el arrecife y el flujo entre mareas es más débil. Las corrientes suaves levantan menos sedimento y hacen que nadar sea más seguro.</p>

<h2>Hora del día: las mañanas son más tranquilas</h2>
<p>El viento normalmente aumenta durante el día. Menos viento significa olas más pequeñas, superficie más lisa y mejor visibilidad, por eso la primera mitad de la mañana suele ser la mejor ventana.</p>

<h2>Temporada: agua cálida y tiempo estable</h2>
<p>La temporada ideal depende del destino, pero conviene buscar agua cómoda, normalmente entre 20 y 30&nbsp;&deg;C, y periodos sin grandes temporales ni mar de fondo. Muchos destinos tienen meses claramente mejores.</p>

<h2>Compruébalo con un pronóstico en vivo</h2>
<p>No hace falta adivinar. SnorkelForecast puntúa cada hora con luz según oleaje, viento, temperatura del agua, marea y corriente. Abre tu destino para ver la mejor ventana de snorkel de hoy y los mejores meses para visitarlo.</p>
"""
        ),
    },
    {
        "slug": "snorkeling-water-temperature",
        "title": "Qué temperatura del agua es buena para hacer snorkel",
        "summary": (
            "La mayoría de personas hacen snorkel cómodamente entre 20 y 30 °C. Por debajo "
            "de eso, un neopreno corto o una camiseta térmica cambia mucho la experiencia."
        ),
        "faqs": [
            {
                "q": "¿Qué temperatura del agua es cómoda para hacer snorkel?",
                "a": (
                    "La mayoría de snorkelers se sienten cómodos entre 20 y 30 °C. Entre "
                    "25 y 28 °C suele bastar con bañador. Entre 18 y 22 °C ayuda un shorty "
                    "o una camiseta térmica, y por debajo de 18 °C conviene neopreno."
                ),
            },
            {
                "q": "¿El agua a 20 °C es demasiado fría?",
                "a": (
                    "20 °C es fresca, pero puede valer para una salida corta, sobre todo con "
                    "protección térmica. Si empiezas a tiritar, sal del agua y entra en calor."
                ),
            },
            {
                "q": "¿Cómo compruebo la temperatura del agua antes de ir?",
                "a": (
                    "Usa un pronóstico de temperatura superficial del mar para el punto exacto. "
                    "SnorkelForecast muestra la temperatura actual y reciente junto con olas, viento y mareas."
                ),
            },
        ],
        "body": mark_safe(
            """
<p>La temperatura del agua puede decidir una salida de snorkel. El cuerpo pierde calor mucho más rápido en el agua que en el aire, así que una temperatura que parece aceptable para un baño rápido puede sentirse fría al flotar durante un rato.</p>

<h2>Guía rápida de temperatura</h2>
<ul>
  <li><strong>28-30&nbsp;&deg;C</strong>: agua tropical muy cálida; normalmente basta con bañador.</li>
  <li><strong>25-28&nbsp;&deg;C</strong>: ideal para la mayoría de personas.</li>
  <li><strong>22-25&nbsp;&deg;C</strong>: cómoda, aunque una lycra añade calor y protección solar.</li>
  <li><strong>18-22&nbsp;&deg;C</strong>: fresca; un neopreno corto ayuda a estar más tiempo.</li>
  <li><strong>Menos de 18&nbsp;&deg;C</strong>: fría; usa neopreno y limita la sesión.</li>
</ul>

<h2>Qué llevar</h2>
<p>Una camiseta de protección solar reduce quemaduras y quita algo de frío. Un neopreno corto funciona bien en agua templada-fresca, y un neopreno completo de 3&nbsp;mm o más es mejor por debajo de unos 20&nbsp;&deg;C.</p>

<h2>Por qué importa el pronóstico</h2>
<p>La temperatura cambia mucho por zona y época del año. Consulta la temperatura actual del mar para tu lugar concreto antes de salir, junto con oleaje, viento y marea.</p>
"""
        ),
    },
    {
        "slug": "best-snorkeling-destinations",
        "title": "Los mejores destinos de snorkel del mundo",
        "summary": (
            "Del Gran Arrecife de Barrera y Maldivas a Hawái, el mar Rojo y el Caribe: "
            "una guía de grandes destinos de snorkel y cómo revisar sus condiciones en vivo."
        ),
        "faqs": [
            {
                "q": "¿Dónde está el mejor snorkel del mundo?",
                "a": (
                    "Entre los destinos más conocidos están Australia, Maldivas, el mar Rojo, "
                    "Hawái, Raja Ampat, Galápagos, Palau y arrecifes del Caribe como Bonaire, Cozumel y Belice."
                ),
            },
            {
                "q": "¿Qué hace bueno a un destino de snorkel?",
                "a": (
                    "Agua clara y cálida, bahías o arrecifes protegidos, vida marina abundante "
                    "y acceso fácil. En el día a día, lo que más cambia la experiencia son las condiciones."
                ),
            },
        ],
        "body": mark_safe(
            """
<p>El mundo está lleno de lugares extraordinarios para hacer snorkel, pero la diferencia entre una salida inolvidable y una decepcionante suele estar en <strong>elegir el sitio y el momento correctos</strong>.</p>

<h2>Pacífico y Hawái</h2>
<ul>
  <li><a href="/es/estados-unidos/maui/">Maui, Hawái</a>: tortugas y arrecifes accesibles desde playas fáciles.</li>
  <li><a href="/es/estados-unidos/hanauma-bay/">Hanauma Bay, Oahu</a>: arrecife protegido en un cráter volcánico.</li>
  <li><a href="/es/french-polynesia/moorea/">Moorea</a> y <a href="/es/french-polynesia/bora-bora/">Bora Bora</a>: lagunas cálidas con rayas y tiburones de arrecife.</li>
</ul>

<h2>Australia y el Gran Arrecife de Barrera</h2>
<ul>
  <li><a href="/es/australia/ningaloo-reef/">Ningaloo Reef</a>: arrecife cerca de la playa y posibilidad de ver tiburones ballena.</li>
  <li><a href="/es/australia/lady-elliot-island/">Lady Elliot Island</a> y <a href="/es/australia/heron-island/">Heron Island</a>: cayos coralinos con agua clara.</li>
</ul>

<h2>Sudeste asiático e Índico</h2>
<ul>
  <li><a href="/es/indonesia/raja-ampat/">Raja Ampat</a>: una de las zonas con mayor biodiversidad marina del planeta.</li>
  <li><a href="/es/maldives/maafushi/">Maldivas</a>: arrecifes de casa, mantas y tortugas cerca de muchas islas.</li>
</ul>

<h2>Mar Rojo y Caribe</h2>
<ul>
  <li><a href="/es/egypt/sharm-el-sheikh/">Sharm El Sheikh</a> y <a href="/es/egypt/dahab-blue-hole/">Dahab</a>: coral directo desde la costa.</li>
  <li><a href="/es/bonaire/kralendijk/">Bonaire</a>, <a href="/es/mexico/cozumel/">Cozumel</a> y <a href="/es/belize/hol-chan/">Hol Chan</a>: arrecifes caribeños de referencia.</li>
</ul>

<h2>Antes de ir</h2>
<p>La regla se repite en casi todos los destinos: busca una mañana calmada, cerca de la pleamar, con poco viento y poca ola. Abre cualquier destino para ver su puntuación de snorkel en las próximas 72 horas o <a href="/es/destinos/">explora todos los países</a>.</p>
"""
        ),
    },
    {
        "slug": "best-snorkeling-in-greece",
        "title": "Mejor snorkel en Grecia: islas y lugares destacados",
        "summary": (
            "Las aguas claras del Egeo y el Jónico hacen de Grecia uno de los mejores "
            "destinos de snorkel de Europa. Estos son los lugares clave y cómo revisar condiciones."
        ),
        "faqs": [
            {
                "q": "¿Dónde está el mejor snorkel en Grecia?",
                "a": (
                    "Algunos de los mejores lugares están en las islas Jónicas, las Cícladas, "
                    "Rodas y Creta, con calas rocosas protegidas y buena visibilidad."
                ),
            },
            {
                "q": "¿Cuándo es mejor hacer snorkel en Grecia?",
                "a": (
                    "De junio a septiembre, cuando el mar está más cálido y suele estar más calmado. "
                    "En las Cícladas conviene ir por la mañana antes del viento meltemi."
                ),
            },
        ],
        "body": mark_safe(
            """
<p>Con agua cálida, mucha visibilidad y miles de calas protegidas, <strong>Grecia es uno de los mejores destinos de snorkel de Europa</strong>. La mayoría de lugares son calas rocosas y aguas claras donde se ven peces, pulpos y, con suerte, tortugas.</p>

<h2>Islas Jónicas</h2>
<ul>
  <li><a href="/es/greece/zakynthos/">Zakynthos</a>: cuevas azules, calas claras y posibilidad de ver tortugas.</li>
  <li><a href="/es/greece/kefalonia/">Kefalonia</a>: bahías turquesas y playas de guijarros protegidas.</li>
  <li><a href="/es/greece/lefkada/">Lefkada</a> y <a href="/es/greece/corfu/">Corfu</a>: agua clara y fondos rocosos accesibles.</li>
</ul>

<h2>Cícladas</h2>
<ul>
  <li><a href="/es/greece/milos/">Milos</a>: formaciones volcánicas y calas transparentes.</li>
  <li><a href="/es/greece/paros/">Paros</a> y <a href="/es/greece/naxos/">Naxos</a>: bahías arenosas y aguas luminosas.</li>
  <li><a href="/es/greece/santorini/">Santorini</a>: fondos volcánicos y agua cálida en verano.</li>
</ul>

<h2>Dodecaneso y Creta</h2>
<ul>
  <li><a href="/es/greece/rhodes/">Rodas</a>: Anthony Quinn Bay es una cala clásica para snorkel.</li>
  <li><a href="/es/greece/kos/">Kos</a>, <a href="/es/greece/symi/">Symi</a> y <a href="/es/greece/crete/">Creta</a>: calas claras, cuevas y agua cálida.</li>
</ul>

<h2>Planifica según las condiciones</h2>
<p>El verano griego suele ser estable, pero el viento de la tarde puede levantar el mar. Busca la mañana y la pleamar para mejor visibilidad. También puedes <a href="/es/greece/">ver todos los lugares de Grecia que pronosticamos</a>.</p>
"""
        ),
    },
    {
        "slug": "best-snorkeling-in-hawaii",
        "title": "Mejor snorkel en Hawái: lugares por isla",
        "summary": (
            "Hawái tiene algunos de los mejores lugares de snorkel para principiantes, con "
            "tortugas, peces de arrecife y agua clara desde playas de fácil acceso."
        ),
        "faqs": [
            {
                "q": "¿Cuál es el mejor lugar para hacer snorkel en Hawái?",
                "a": (
                    "Destacan Honolua Bay y Molokini en Maui, Hanauma Bay en Oahu, y "
                    "Kealakekua Bay y Two Step en Big Island. El mejor en cada día depende del oleaje y el viento."
                ),
            },
            {
                "q": "¿Cuándo es mejor hacer snorkel en Hawái?",
                "a": (
                    "Temprano por la mañana y, en general, durante los meses de verano, cuando "
                    "el mar en las costas norte suele estar más tranquilo."
                ),
            },
        ],
        "body": mark_safe(
            """
<p><strong>Hawái es uno de los mejores lugares del mundo para hacer snorkel</strong>, con agua cálida, tortugas marinas y peces de arrecife accesibles desde la playa. Las condiciones cambian mucho según isla, costa y temporada, así que conviene revisar el pronóstico exacto.</p>

<h2>Maui</h2>
<ul>
  <li><a href="/es/estados-unidos/honolua-bay/">Honolua Bay</a>: reserva marina con coral vivo, mejor en mañanas calmadas.</li>
  <li><a href="/es/estados-unidos/molokini-crater/">Molokini Crater</a>: cráter volcánico con gran visibilidad.</li>
  <li><a href="/es/estados-unidos/kaanapali-beach/">Kaanapali</a>, <a href="/es/estados-unidos/napili-bay/">Napili Bay</a> y <a href="/es/estados-unidos/kapalua-bay/">Kapalua Bay</a>: playas fáciles y frecuentes tortugas.</li>
</ul>

<h2>Oahu y Big Island</h2>
<ul>
  <li><a href="/es/estados-unidos/hanauma-bay/">Hanauma Bay</a>: arrecife protegido dentro de un cono volcánico.</li>
  <li><a href="/es/estados-unidos/kealakekua-bay/">Kealakekua Bay</a>: santuario marino con coral sano.</li>
  <li><a href="/es/estados-unidos/two-step-honaunau/">Two Step</a>: entrada desde lava y arrecife lleno de vida.</li>
</ul>

<h2>Comprueba antes de ir</h2>
<p>La regla de oro en Hawái es hacer snorkel por la mañana, cerca de pleamar y antes de que suban viento y surf. Abre cualquier lugar para ver la puntuación de hoy, la próxima buena ventana y los mejores meses. O <a href="/es/estados-unidos/">consulta todos los lugares de Hawái y Estados Unidos que pronosticamos</a>.</p>
"""
        ),
    },
]

GUIDES_BY_SLUG = {g["slug"]: g for g in GUIDES}
GUIDES_ES_BY_SLUG = {g["slug"]: g for g in GUIDES_ES}


def _active_language() -> str:
    language_code = translation.get_language() or "en"
    return "es" if language_code.startswith("es") else "en"


def get_guides() -> list[dict]:
    guides = GUIDES_ES if _active_language() == "es" else GUIDES
    return [deepcopy(guide) for guide in guides]


def get_guide(slug: str) -> dict | None:
    guides_by_slug = GUIDES_ES_BY_SLUG if _active_language() == "es" else GUIDES_BY_SLUG
    guide = guides_by_slug.get(slug)
    return deepcopy(guide) if guide else None
