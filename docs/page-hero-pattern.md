# Page Hero Pattern

This document captures how we design and implement hero blocks across Tailux admin pages. The component lives in `apps/web/src/shared/ui/patterns/PageHero.tsx`; we treat the Storybook stories as interactive examples, while this note holds the contract and UX rules.

## Purpose
- Give instant context: page name, short summary, and navigation breadcrumbs.
- Highlight the 3–4 most critical signals before the user scans the rest of the page.
- Surface one primary action (and, optionally, one secondary) so the user can react immediately.
- Optionally expose first-layer filters that change the data shown directly under the hero.

If a screen does not need these outcomes (for example a pure list or form page) we do not ship a hero; a compact header or standard title is enough.

## Variants
- `default`: cinematic feel for high-level dashboards or onboarding experiences. Uses gradient background and generous spacing.
- `metrics`: data-first variant for operational and observability pages. Background is darker, grid emphasizes metrics, and text stays concise.
- `compact`: tight header for nested settings, library pages, or modal-like flows. Minimal spacing and neutral background.

Choose the variant per screen; do not mix more than one hero per page.

## Layout Anatomy
```
┌────────────────────────────────────────────────────────────┐
│ Eyebrow / Breadcrumbs                                      │
│ Title + Description            Primary & Secondary actions │
│ Filters (optional)                                         │
│ Metrics grid (optional)                                    │
│ Children slot (optional alerts, tabs, callouts)            │
└────────────────────────────────────────────────────────────┘
```
- Title stays within two lines; longer copy moves into the description or below the hero.
- Primary actions align to the right (or under the title on mobile). Secondary and tertiary actions collapse into an overflow menu.
- Filters live inside the hero only when they are required before reading the main view; otherwise show them under the hero.

## Metrics Guidelines
- Cap the visible metrics at four items on desktop. If stakeholders insist on more, provide an expandable “Show more” set inside the hero or move the excess into the main body.
- Each metric includes a label, value, and optional delta (`trend`) or helper text. Deltas use the `accent` token to reinforce meaning.
- Metric values prefer compact numerals: thousands separators with thin spaces, `–` dash for missing data, and no more than two decimals.
- Loading and error states rely on the shared skeleton/error primitives to avoid layout shifts.

## Actions and Filters
- One primary CTA is required when the page expects immediate interaction (e.g., “Add model”). Secondary CTA is optional; all other actions go into an overflow dropdown.
- Filters follow the order: high-frequency chips → dropdowns → search input (rightmost control). Include a visible reset action.
- Persist filter state in the URL query string so deep links remain accurate.

## Adaptivity
- Desktop (`≥1280px`): metrics render in a single row of up to four tiles.
- Tablet (`768–1279px`): grid falls back to two columns; secondary actions collapse into overflow.
- Mobile (`<768px`): hero becomes a single column, with CTA rendered as a sticky action bar right below the hero when necessary.

## Data Ownership
- Every metric and action must have a clear owner. Document refresh cadence and telemetry IDs alongside the API contract.
- When data is stale for more than five minutes, expose a timestamp pill and enable a `Refresh` action.

## Implementation Checklist
- Update Storybook stories whenever you add a new preset or change props. Keep Chromatic snapshots in sync.
- Instrument hero interactions with `data-analytics="hero:<slug>"` wrappers so analytics stays consistent.
- When adding a new hero to a screen, cross-check the rest of the layout to prevent duplicate metrics or actions lower on the page.
- If you disable the hero on a given screen, remove leftover metric cards or CTA slots so the top of the page stays clean.
