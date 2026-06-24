No — I had enough to diagnose it. I found a clear pattern: **the page is trying to be a forecast app, SEO landing page, data dashboard, educational guide, FAQ, trend report, and raw data table all at once.** That is hurting both perceived speed and mobile usefulness.

## The 10x version

The mobile page should answer one question in under 5 seconds:

> **“Can I snorkel here today, and when is the best window?”**

Everything else should be secondary, collapsed, or loaded only when requested.

Right now, the live Carboneras page shows a summary, daily outlook, chart sections, tides, recent averages, seasonal trends, FAQs, 24h/72h condition trends, a 72-hour forecast grid, methodology, and a detailed hourly table on the same page. The extracted page content shows the 72-hour grid alone producing dozens of repeated “poor” forecast cells before the detailed table begins. ([SnorkelForecast.com][1])

## Biggest problems I found

### 1. The page has too much information before the useful decision

For Carboneras, the page already knows the answer: **0 excellent, 0 good, 0 fair, 69 poor hours**, and “No safe snorkeling window is expected in the next 72 hours.” ([SnorkelForecast.com][1])

But instead of making that the whole above-the-fold experience, the user gets pushed into charts, tide lists, recent averages, seasonal trends, FAQs, grids, methodology, and a full data table. On mobile, that means too much scrolling and too much interpretation.

**10x fix:** make the first viewport a decision card:

```text
Carboneras today
❌ Do not snorkel

Why:
Waves 0.7m — too high
Wind 11.0 m/s — too strong
Sea temp 14.9°C — cold

Next check:
No safe window in next 72h

Best months:
September–November
```

Then give the user three large actions:

```text
[Show best hours] [Show tides] [Why poor?]
```

This alone would massively improve information accessibility.

---

### 2. Too many charts are present on one page

The template includes separate chart sections for 24h score, 72h score, seasonal trends, sea temperature, 24h wave/wind/tide, and 72h wave/wind/tide. That is a lot of canvas work for a page whose primary user task is a yes/no decision.

You are lazy-loading Chart.js with `IntersectionObserver`, which is good. But once any chart intersects, `loadAndInit()` runs and `initCharts()` creates all charts, not just the chart the user reached. The target list includes ten charts, and the observer triggers one global load/init.

**10x fix:** do not initialize all charts at once. Either:

1. Replace most charts with lightweight HTML summaries on mobile.
2. Render only the first relevant chart.
3. Initialize each chart independently when its own card opens or enters the viewport.
4. Put “Condition Trends” behind a `<details>` or “Advanced forecast” tab.

For mobile, I would remove the 72h score chart entirely and use a compact day-card layout instead.

---

### 3. The charts duplicate the forecast grid and table

The page has:

* Snorkel Score next 24h
* Snorkel Score next 72h
* Condition Trends next 24h
* Condition Trends next 72h
* 72-hour forecast overview
* Detailed hourly conditions table

That is six ways of saying roughly the same thing. The live page’s 72-hour grid currently outputs repeated hour cells like “Wed 00:00 poor”, “Wed 01:00 poor”, and so on for many lines. ([SnorkelForecast.com][1])

**10x fix:** collapse this into three layers:

```text
Layer 1: Decision
Can I snorkel? Best window? Why/why not?

Layer 2: Planner
Today / Tomorrow / Day 3 cards with best time block and blockers.

Layer 3: Advanced
Charts + raw hourly table, collapsed by default.
```

The full hourly table should stay for SEO and power users, but it should not be a primary mobile UI.

---

### 4. The base layout loads multiple fonts and sitewide scripts everywhere

The base template preconnects to Google Fonts and loads three font families: Instrument Serif, Hanken Grotesk, and Spline Sans Mono. It also loads theme, nav, autocomplete, and search JavaScript sitewide.

That may be fine on desktop, but on mobile forecast pages every non-essential request competes with rendering the answer. Google’s LCP guidance says the main content should render quickly, with good LCP at 2.5 seconds or less for at least 75% of visits, and high TTFB or render-blocking assets can make that difficult. ([web.dev][2])

**10x fix:**

* Use system fonts on forecast pages, or self-host one variable font.
* Remove the serif and mono fonts from forecast pages unless visibly required.
* Load autocomplete/search JS only on pages with a search input.
* Keep theme/nav JS tiny and inline only the critical part if needed.
* Add a hard performance budget: forecast page JS under 50KB initial, CSS under 30KB initial.

---

### 5. The backend still has a slow-path risk on cache miss

The forecast fetcher is well thought out: it uses cache, stale cache, negative cache, DB fallback, and parallel Open-Meteo requests. But the request path can still call two external APIs on a cache miss: marine and weather.

It also computes recent averages, monthly scores, and monthly SST in the location view before rendering.

**10x fix:** make location pages fully DB-backed and precomputed.

The page request should not need to call Open-Meteo or calculate monthly aggregates. It should read one compact `LocationForecastSnapshot` row, for example:

```python
LocationForecastSnapshot:
  location
  generated_at
  expires_at
  verdict
  next_good_window_start
  next_good_window_end
  primary_blockers
  daily_cards_json
  tide_summary_json
  hourly_json
  seasonal_summary_json
```

Then a background job refreshes snapshots. The page becomes a fast database read plus template render. This turns cache-miss latency from “external API + computation risk” into “read one row”.

---

## Recommended mobile IA redesign

### Above the fold

Replace the current long summary with a strong “forecast verdict” module.

```html
<section class="forecast-hero">
  <p class="eyebrow">Carboneras · Updated 23 Jun 2026, 23:00 CET</p>

  <div class="verdict verdict--poor">
    <div class="verdict-icon">❌</div>
    <div>
      <h1>Do not snorkel today</h1>
      <p>No safe window is forecast in the next 72 hours.</p>
    </div>
  </div>

  <div class="reason-grid">
    <div>
      <span>Waves</span>
      <strong>0.7 m</strong>
      <small>Too high</small>
    </div>
    <div>
      <span>Wind</span>
      <strong>11.0 m/s</strong>
      <small>Too strong</small>
    </div>
    <div>
      <span>Water</span>
      <strong>14.9°C</strong>
      <small>Cold</small>
    </div>
  </div>
</section>
```

For a good forecast, the same card becomes:

```text
✅ Good window today
Best: 09:00–11:00
Why: low waves, light wind, near high tide
```

### Next section: 3-day planner

Use cards, not charts:

```text
Today
Poor all day
Main blocker: wind

Tomorrow
Poor all day
Main blocker: waves

Friday
Poor all day
Main blocker: waves + wind
```

This is far easier than a 72-cell grid on mobile.

### Next section: “Best available hours”

Even when there is no good window, users still want the least-bad option.

```text
Calmest available periods
Wed 18:00 — waves 0.54m, wind 5.9m/s
Wed 19:00 — waves 0.56m, wind 5.6m/s
```

That is more useful than showing all 69 hours.

### Advanced sections

Use collapsible sections:

```text
▸ Hourly forecast table
▸ Wave, wind and tide charts
▸ Seasonal trends
▸ How scoring works
▸ FAQs
```

The detailed table is already inside `<details>` in the repo version, which is good.  I would extend that pattern to most chart-heavy and SEO-heavy content on mobile.

---

## Performance changes in priority order

### P0: Make the first render tiny

The initial HTML should contain only:

* breadcrumb
* title
* verdict card
* three blocker metrics
* 3-day planner
* “last updated”
* links/anchors to advanced sections

Everything else can be below-the-fold or dynamically loaded.

Target:

```text
Mobile LCP: <2.0s
Initial JS: <50KB
Initial CSS: <30KB
Server TTFB cached: <200ms
Server TTFB uncached: <500ms
```

Google recommends focusing on real-user LCP data, with 2.5 seconds or less as the good threshold. ([web.dev][2])

### P1: Split chart initialization

Current behavior: first chart enters viewport → Chart.js loads → all charts initialize.

Better behavior:

```js
function observeChart(canvas, buildConfig) {
  const io = new IntersectionObserver((entries) => {
    if (!entries.some(e => e.isIntersecting)) return;
    io.disconnect();

    import('/static/js/chart.umd.min.js').then(() => {
      new Chart(canvas, buildConfig());
    });
  }, { rootMargin: '150px' });

  io.observe(canvas);
}
```

Or simpler: render charts only after the user taps “Show charts”.

Chart.js itself recommends performance techniques like reducing main-thread work, using OffscreenCanvas where appropriate, and disabling expensive line/point drawing when there are many points. ([chartjs.org][3])

### P2: Remove duplicate 24h/72h chart pairs

On mobile:

* Keep one compact “score by day” visualization.
* Remove separate 24h and 72h versions.
* Replace wave/wind/tide chart triplets with metric chips and “show chart” toggles.

### P3: Load search/autocomplete only where needed

In `base.html`, `autocomplete.min.js` and `search.js` are loaded on every page.  Move them into a `{% block scripts %}` used only on search pages or pages with a search box.

### P4: Use precomputed forecast snapshots

The backend already tries DB before API.  Take that further: never let a public location page call external APIs synchronously. A scheduled task should refresh all forecast snapshots, and the page should serve stale-but-marked data if refresh fails.

### P5: Reduce font cost

Use:

```css
font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

for forecast pages. Add brand fonts later, non-blocking, only if they materially improve the experience.

---

## Better information design

### Replace “Forecast Summary” with “Decision Summary”

Current copy:

> “Over the next 69 hours… conditions will vary across excellent, good, fair and poor periods…”

But if all 69 are poor, the user does not need that sentence. The page should say:

```text
No safe snorkeling window in the next 72 hours.

Main reasons:
• Wind is above the safe threshold.
• Waves are above the safe threshold.
• Sea temperature is below comfort range.
```

The thresholds are already available in your model: wave height under 0.36m, wind below 5.4m/s, sea surface temperature between 20.6°C and 30.4°C, and slack/current criteria.

### Add “why not?” explanations per hour/day

Right now you color bad table values red, but mobile users need plain language.

For each day, compute top blockers:

```python
blockers = {
    "waves": count of hours where not wave_ok,
    "wind": count of hours where not wind_ok,
    "temperature": count of hours where not sst_ok,
    "tide/current": count of hours where not slack_ok,
    "darkness": count of hours where not light_ok,
}
```

Then show:

```text
Thursday: Poor
Main blocker: strong wind
Secondary blocker: high waves
```

### Show “best available” even when nothing is good

This is probably the highest-value UX improvement. A tourist may still be deciding whether to go to the beach, postpone, or pick another nearby spot.

Add:

```text
Least bad window:
Wed 18:00–19:00
Still not recommended: waves/wind remain above ideal.
```

### Add comparison to nearby spots

You already fetch nearby locations for internal linking.  Make that more useful:

```text
Carboneras looks poor. Nearby spots:
Mojácar — fair tomorrow morning
Cabo de Gata — poor
Aguadulce — good Thursday 09:00
```

This turns a dead-end “do not snorkel” page into a planning tool.

---

## Accessibility improvements

### 1. Do not rely on color-only forecast cells

The 72-hour grid uses green opacity based on score.  That is hard for low-vision users, color-blind users, and mobile users in glare.

Use text labels and icons:

```text
Good  ✅
Fair  ⚠️
Poor  ❌
```

### 2. Improve tap targets

On mobile, every expandable section and action should be at least 44px high. The forecast cells are visually dense; day cards are easier to tap.

### 3. Use accessible chart alternatives

Every chart should have a summary immediately before it:

```text
Wave trend: waves increase from 0.6m Wednesday to 2.4m Friday, making conditions worse.
```

Then the canvas becomes optional rather than essential.

### 4. Add skip links

Add:

```html
<a href="#forecast-verdict" class="skip-link">Skip to forecast</a>
<a href="#hourly" class="skip-link">Skip to hourly table</a>
```

### 5. Use semantic status

For the verdict:

```html
<section role="status" aria-live="polite">
```

or just a clear heading if the content is static.

---

## Concrete implementation plan

### Phase 1: One-day template refactor

Change the top of `location_forecast.html` to this order:

```text
1. Breadcrumb
2. Verdict card
3. Metric blocker cards
4. 3-day outlook cards
5. Best available / next good window
6. Tides
7. Nearby alternatives
8. Advanced sections
```

Move these below `<details>`:

```text
- Snorkel Score charts
- Seasonal charts
- Condition Trends charts
- 72-hour grid
- Detailed table
- Methodology
- FAQs
```

### Phase 2: Backend summary fields

In `location_forecast`, compute:

```python
primary_blockers
daily_cards
best_available_window
next_update_time
forecast_freshness
```

Example structure:

```python
def summarize_blockers(hours):
    checks = [
        ("waves", lambda h: not h.get("wave_ok")),
        ("wind", lambda h: not h.get("wind_ok")),
        ("water temperature", lambda h: not h.get("sst_ok")),
        ("tide/current", lambda h: not h.get("slack_ok")),
        ("daylight", lambda h: not h.get("light_ok")),
    ]

    counts = []
    for label, failed in checks:
        counts.append((label, sum(1 for h in hours if failed(h))))

    return [
        {"label": label, "count": count}
        for label, count in sorted(counts, key=lambda x: x[1], reverse=True)
        if count
    ][:3]
```

### Phase 3: Chart-on-demand

Do not render ten `<canvas>` elements on initial mobile view. Render buttons:

```html
<button data-chart="score">Show score chart</button>
<button data-chart="wave">Show wave chart</button>
<button data-chart="wind">Show wind chart</button>
```

Then create the canvas only after click.

### Phase 4: Snapshot model

Add a precomputed snapshot table and use it as the primary render source. The current code’s cache/stale/DB fallback is already moving in the right direction, but location pages should be safe even on cold starts.

---

## What I would remove or demote

Remove from initial mobile view:

* 72h score chart
* duplicate 24h and 72h trend charts
* seasonal chart
* sea temperature annual chart
* full 72-hour grid
* full hourly table
* methodology
* FAQ block

Keep, but collapsed:

* detailed hourly data
* scoring explanation
* charts
* seasonal content

Keep visible:

* verdict
* next good window / no window
* reasons
* best available hours
* tides
* nearby alternatives

---

## Highest-impact “10x” change

Build the page around this hierarchy:

```text
Can I snorkel?
↓
When?
↓
Why / why not?
↓
What should I do instead?
↓
Show me the data
```

Right now the page is closer to:

```text
Here is all the data
↓
You figure out whether snorkeling is good
```

That is the core UX issue. Performance work will help, but the largest improvement is changing the page from a **data report** into a **decision assistant**.

[1]: https://snorkelforecast.com/spain/carboneras/ "Carboneras, Spain – Snorkel Forecast"
[2]: https://web.dev/articles/optimize-lcp "Optimize Largest Contentful Paint  |  Articles  |  web.dev"
[3]: https://www.chartjs.org/docs/latest/general/performance.html "Performance | Chart.js"

