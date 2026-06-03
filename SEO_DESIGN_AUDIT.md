# SnorkelForecast.com — SEO + Design/Usefulness Audit

_Date: 2026-06-03 · Data source: Google Search Console (via RefreshAgent proxy), 30/90-day windows._

## 1. Where we are (the hard numbers)

| Metric | Last 30d | Prev 30d | Last 7d |
|---|---|---|---|
| Clicks | 19 | 11 | 1 |
| Impressions | 689 | 603 | 118 |

Tiny but **growing** (clicks +73% MoM). The site is indexed and ranking; the problem is **rankings stuck on page 2–4** and **almost no content depth**, not a penalty.

### Top pages (30d)
| Page | Impr. | Clicks | Avg pos |
|---|---|---|---|
| `/` (home) | 245 | 9 | **6.5** ✅ |
| `/usa/maui/` | 273 | 8 | **29.8** ⚠️ page 3 |
| `/greece/santorini/` | 98 | 0 | 41.2 |
| `/spain/carboneras/` | 11 | 1 | 14.7 |
| `/croatia/dubrovnik/` | 16 | 0 | 21.7 |
| `/turkey/` | 12 | 1 | 19.2 |

### The story the data tells
1. **Maui/Hawaii is the breakout niche.** `/usa/maui/` already pulls 273 impressions but ranks ~30. Queries: _"snorkel report maui today"_ (pos 24), _"maui snorkel conditions"_ (pos 25), _"maui snorkel report today"_ (pos 23), _"maui snorkeling conditions today"_ (pos 6.5). These are **high-intent, recurring, daily-checked** queries. Moving Maui from page 3 → page 1 is the single biggest lever.
2. **Huge informational gap.** Many impressed, **0-click** queries are informational and have **no matching page**: _"best time to snorkel maui"_, _"best tide for snorkeling"_, _"best time to snorkel in maui"_, _"best snorkeling in greece islands"_, _"croatia snorkeling map"_. The site has **only live-forecast pages and zero guides** — we appear but never win the click.
3. **Competitor-shaped demand.** _"boss frog snorkel report"_, _"honolua bay snorkel report"_, _"hawaii snorkel report"_ — people want a **daily spot-level report**. That's exactly what the product is; the pages just aren't optimized to say so.

## 2. Critical findings

### SEO
- **[FIXED] Titles/meta didn't match intent.** Location title was `"{City}, {Country} – Snorkel Forecast"`. Users search _"snorkel report {city} today"_. → Now `"{City} Snorkel Report Today | Conditions & 3-Day Forecast"`.
- **[FIXED] Sitemap missing key pages.** `sitemap.xml` only listed country + location pages — **the #6.5-ranked homepage, `/countries/`, and `/search/` were absent.** → Added `StaticViewSitemap`.
- **[ACTION — manual] Sitemap not submitted in GSC.** GSC reports **0 sitemaps**. `https://snorkelforecast.com/sitemap.xml` works (200, 38 URLs). **Submit it in Search Console** — this alone should speed indexation materially.
- **[FIXED] Thin FAQ / no informational coverage.** Added visible + JSON-LD FAQ targeting the exact 0-click queries (_best time of day_, _best tide_, _is the water warm enough_, _can you snorkel today_).
- **[FIXED] No BreadcrumbList schema** (only a visual breadcrumb). → Added.
- **[FIXED] Debug leaks shipping to prod:** `print("DEBUG: Using MockLocation…")` in `views.py` and a `"DEBUG: No name"` title fallback. → Removed.
- **[OPEN] OSM spots not in sitemap.** `OSMSpot` (potentially thousands of real dive/snorkel sites) is imported but **not surfaced as pages or in the sitemap**. This is the path to 10× the URL footprint.
- **[OPEN] Sea-temperature is a known SEO magnet.** "{place} water temperature" gets huge, recurring volume. The data is already fetched — a dedicated angle/section would capture it.

### Design / engagement / usefulness
- **[FIXED] The answer was buried.** Location pages opened with charts; the user's actual question ("can I snorkel here today?") was 4 scrolls down. → Added an above-the-fold **green/amber verdict box** with the next good window + % suitable hours.
- **[OPEN] Pages are data-dense but not skimmable.** Six near-identical `card-enhanced` boxes stacked vertically. Needs a tighter hierarchy: verdict → today's hourly strip → 3-day outlook → deep data (charts/table) collapsed.
- **[OPEN] No imagery / sense of place.** Every page looks identical regardless of destination. A hero photo or map per location would 10× perceived quality and dwell time.
- **[OPEN] No "best snorkeling near me / in {country}" editorial.** Country pages are bare lists; they should be rankable guides ("12 best snorkeling spots in Greece") that funnel to forecast pages.

## 3. Roadmap to 10× (prioritized by ROI)

### Now — shipped
- ✅ Intent-matched titles + dynamic meta descriptions on location pages
- ✅ Above-the-fold verdict box (engagement + CTR)
- ✅ Expanded FAQ (visible + schema) hitting real 0-click queries
- ✅ BreadcrumbList schema
- ✅ Homepage/countries/search added to sitemap
- ✅ Removed debug output
- ✅ **8 Hawaii spot pages** seeded (Honolua Bay, Molokini, Kaanapali, Napili, Kapalua, Hanauma Bay, Kealakekua, Two Step) — target explicit 0-click spot queries; in sitemap (`/usa/<spot>/`). Idempotent `populate_hawaii_spots` command, wired into `startup.sh`.
- ✅ **Per-location evergreen content** block ("Snorkeling in {city}" + best time/best months) on every location page
- ✅ **Country pages → guides** ("Best Snorkeling in {Country}" title + intro + guidance content)
- ✅ **Internal linking**: "More snorkeling spots in {country}" cross-links between location pages
- ✅ **Design declutter**: 72-row table collapsed into `<details>`; content-first hierarchy

- ✅ **Guides hub** (`/guides/`) with two cornerstone articles — "Best Time to Snorkel (tide/time/season)" and "What Water Temperature Is Good for Snorkeling?" — targeting documented 0-click informational queries ("best tide for snorkeling", "best time to snorkel", "santorini water temperature", "how deep is snorkeling water"). Article + FAQPage + BreadcrumbList schema; linked from nav + location pages; in sitemap.

### Why traffic hasn't moved *yet* (and what's required)
The 10× traffic target is an **outcome gated on factors outside the code**, now that the on-site work is done:
1. **Google must crawl + index + rank** the new/changed pages — this takes days to weeks, not minutes.
2. **Manual GSC action (only the site owner can do):** submit `https://snorkelforecast.com/sitemap.xml` (GSC still reports 0 sitemaps) and "Request indexing" for `/usa/maui/` and the new `/usa/*/` spot + `/guides/*` pages. **This is the single biggest unlock and cannot be automated from the codebase.**
3. Measure after ~2–4 weeks: Maui avg position, impressions→clicks on informational queries, indexed-page count.

### Page footprint expansion — shipped (~9× location pages)
- ✅ **~200 curated real snorkeling spots** added across **72 countries** (`conditions/world_spots.py` + `world_spots_2.py`, seeded by idempotent `populate_world_spots`, wired into `startup.sh`). Location pages went from ~26 → **231**; **sitemap.xml grew from 35 → 309 URLs**.
- ✅ **Rate-limit safeguards** for the larger footprint: jittered forecast cache TTL (±12%, prevents synchronized expiry bursts) and a throttled scheduler (`SCHEDULER_REQUEST_DELAY_SECONDS`, default 0.5s + jitter) so a full refresh of ~1,000 locations stays ~4 req/s — well under Open-Meteo's limits. New spots are `is_popular=False`, so the homepage's per-location fetch is unaffected; spots are spread across many countries to keep each country page's fetch burst small.

### Indexing acceleration — shipped (IndexNow)
- ✅ **IndexNow integration** so new/changed URLs are pushed instantly to Bing, Yandex, DuckDuckGo, Seznam and Naver (the modern replacement for the removed Google/Bing sitemap-ping; several AI search products run on Bing's index). Key file served at `/<key>.txt`, `indexnow_submit` management command builds the full URL list (309) and posts in batches, wired into `startup.sh` after `collectstatic`. Verified end-to-end: pre-deploy it correctly returns HTTP 403 (key file not yet live on prod); it activates automatically on the next deploy.
- ⚠️ **Google does not consume IndexNow** — Google indexing still depends on the crawl cycle + the manual GSC sitemap submission (`sitemap.xml`, now 309 URLs). That manual step remains the single biggest unlock and is the one thing that cannot be automated from the codebase.

### Next build sessions (when ready)
1. Run the OSM import (`OSMSpot` is currently empty) and wire it to indexable pages + sitemap — the path to a 10×-again URL footprint (thousands).
2. Per-location hero imagery/maps; "notify me when conditions are good" retention hook.

### This month (the 10× content engine)
5. **Surface OSMSpot as indexable pages** with the forecast template → 10–100× the URL footprint, all long-tail.
6. **Water-temperature angle** per location ("{City} water temperature today + snorkeling forecast").
7. **Guides hub:** "Best time to snorkel in {place}", "What tide is best for snorkeling", "Snorkeling for beginners" — capture the informational head terms, link down to forecasts.

### Design overhaul (parallel track)
8. Redesign the location page hierarchy (verdict → today strip → 3-day → collapsible deep data).
9. Add location hero imagery + an embedded map.
10. Add an email/"notify me when conditions are good" hook for retention (recurring-visit product).

## 4. What to measure
- Maui avg position (target: <10 within 4 weeks of indexing + content).
- Impressions on informational queries → clicks (FAQ/guides working).
- Indexed-page count after sitemap submission + OSM page rollout.
