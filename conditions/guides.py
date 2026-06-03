"""Evergreen snorkeling guides.

These cornerstone articles target informational queries that Search Console
shows SnorkelForecast already receives impressions for but had no matching
page to answer (e.g. "best tide for snorkeling", "best time to snorkel",
"snorkeling water temperature", "how deep is snorkeling water").

Content is stored here (not the DB) so guides are version-controlled and
require no migrations. Each guide renders through conditions/templates/
conditions/guide_detail.html.
"""

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
]

GUIDES_BY_SLUG = {g["slug"]: g for g in GUIDES}
