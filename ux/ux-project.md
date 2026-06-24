# Forecast Page Project Tracker

Source of truth: `ux/ux-project.md` (strategy and performance notes)

## Status legend
- [ ] Not started
- [~] In progress
- [x] Implemented

## P0: Decision-first mobile IA
- [x] Put above-the-fold verdict module first: `Can I snorkel today?` and best window.
  - Acceptance: first viewport contains verdict, blocker summary, and a primary next-window statement.
- [x] Add concise decision copy: `good/fair/poor` rationale in plain language (not just percentages).
  - Acceptance: users see why/why not within one screen.
- [x] Add skip links to forecast status and data table anchors.
  - Acceptance: anchors exist and are keyboard-focusable.
- [x] Add `role="status"`/semantic landmarks for verdict section.

## P0: Primary planning layer
- [x] Add 3-day planner cards (today/tomorrow/day 3) with best block + main blocker.
  - Acceptance: each card has day label, quality tag, and blocker reason.
- [x] Add “best available window” block used when no `next_window`.
  - Acceptance: displays the highest-rated upcoming period and reason.
- [x] Add comparison block for nearby spots.
  - Acceptance: at least 3 nearby spots listed with quick status labels (good/fair/poor).

## P1: Chart performance and duplication control
- [x] Remove/soft-demote duplicate 24h/72h metric layers from primary view.
  - Acceptance: first 2–3 visible sections are decision/planning-oriented.
- [x] Convert chart rendering to explicit user-driven loading.
  - Acceptance: no chart script loads until user interacts with a chart button/section.
- [x] Render one primary chart on demand (no all-at-once initialization).
  - Acceptance: loading score chart does not initialize all chart canvases.
- [x] Add `weather` chart fallback only for advanced sections.
  - Acceptance: advanced charts remain available but hidden/collapsed.

## P2: Content hierarchy
- [x] Collapse heavy sections (`72-hour` overview, condition trend tables/charts, scoring methodology, FAQs) into `<details>` or similar.
  - Acceptance: page can be completed at a decision-planning level without scrolling.
- [x] Keep 72-hour table and methodology for SEO/power users only.
  - Acceptance: both remain on page and crawlable.

## P3: Performance of base page assets
- [x] Move `autocomplete.min.js` and `search.js` out of global base include.
  - Acceptance: non-search pages do not request these scripts.
- [x] Keep theme/nav scripts where needed globally; avoid non-essential page script on forecast detail.
  - Acceptance: forecast detail request bundle reduced and no console regressions.
- [x] Switch forecast pages to lightweight/system-first font stack with non-blocking opt-in fonts.
  - Acceptance: no blocking Google Fonts request for forecast detail pages.

## P4: Data processing improvements
- [x] Compute `primary_blockers` and `daily_cards_json` from forecast payload in view.
  - Acceptance: blocks shown with counts for waves/wind/sst/tide/light.
- [x] Include forecast freshness metadata (`generated_at`, next refresh window).
  - Acceptance: visible human-readable last updated line on forecast page.
- [ ] Add precomputed snapshot model for location pages.
  - Acceptance: page render path primarily reads from DB/precomputed row first.

## P5: Accessibility and readability
- [x] Replace color-only cells with icon/text labels in decision and chart alternatives.
  - Acceptance: poor/good/fair states have explicit text in key summary cells.
- [x] Increase tap targets for action buttons/expanders.
  - Acceptance: primary actions meet 44px minimum height.
- [x] Add plain-English chart summary lines before any chart.
  - Acceptance: each visible chart has adjacent one-line interpretation.

## P6: Backend resilience
- [x] Never call external APIs synchronously on cache miss for location pages.
  - Acceptance: cold/empty cache uses precomputed row or stale row + warning state.
- [x] Ensure page stays functional from stale DB data when Open-Meteo fails.
  - Acceptance: no hard failure on API timeout/network errors.

## Implementation backlog and validation checklist
- [x] Add/refresh unit tests for new view helpers (`blockers`, `planner`, `best window`).
- [ ] Add template tests for new decision-first sections and collapsible advanced sections.
- [ ] Smoke test on mobile widths with main decision actions.
- [ ] Update `README`/docs if any behavior changes in forecast page shape.
- [ ] Validate schema/JSON-LD remains intact after template refactor.
