# Admin UI Interaction Rules

I maintain these rules when I design and build admin screens with tables and hero blocks. They keep consistency even when I am the only engineer shipping changes.

## Quick Actions
- I ship quick actions only for flows that users hit weekly or more, complete within two clicks, and do not require extra confirmation text.
- I limit in-row quick actions to three items: primary button, secondary button, overflow menu. Anything beyond that moves into the overflow list.
- Destructive or irreversible actions always open a confirm dialog with clear copy; they never run on the first tap.
- Icons always pair with labels on desktop; on mobile I collapse to icon-only buttons and keep accessible `aria-label` values in code.
- Loading states replace quick actions with disabled skeleton buttons so layout width stays fixed.
- Keyboard support matters: every quick action is reachable with Tab order from top to bottom and triggers with Enter or Space.

## Metrics
- I put the top-three metrics in the hero header; everything else lives in the insights panel lower on the page.
- Numbers show at most two decimals; large values use thin spaces, for example `12 500` and `9 230.45`.
- Every metric callout includes an optional delta badge; if no delta exists I hide the badge rather than showing `0%`.
- When data is stale for more than five minutes I show a timestamp pill and expose `Refresh` as a quick action.
- In loading and error states I reuse the shared `MetricSkeleton` and `MetricError` components so the page never jumps.
- Telemetry tags: `data-analytics="metric:<slug>"` on the wrapper to keep event tracking identical across screens.

## Adaptivity
- Breakpoints: desktop `>=1280px`, tablet `768-1279px`, mobile `<768px`. I test each breakpoint before merging.
- On tablet I stack hero metrics into two rows and move secondary actions into the overflow menu.
- On mobile the hero collapses into a single column with a sticky quick action bar under the header.
- Tables degrade into cards: each card shows the same quick actions at the bottom, and horizontal scroll is never allowed.
- I keep typography tokens consistent across breakpoints; no manual pixel values sneaking in.

## Filters and Search
- Filter bar sits directly under the hero. Primary filters occupy the first row, advanced filters collapse behind `More filters` with a counter badge.
- Search is always the rightmost control in the primary row. Placeholder describes scope, e.g. `Search nodes`.
- Every filter exposes clear reset behavior: a `Reset` text button at the far right on desktop and inside the overflow drawer on mobile.
- I persist filter state per page in the URL query string; no hidden state in local storage.
- Debounce text filters by 350 ms and trigger server calls on blur or Enter to keep typing responsive.
- Empty and error states always reflect the active filters so users understand context.

## Implementation Checklist
- Update Storybook stories for tables and hero blocks when I touch presets or slots.
- Add or adjust Chromatic snapshots for any new preset, quick action variant, or filter layout.
- Verify events in analytics dev tools before closing the task; metrics and quick action events use consistent naming.
- Document any new preset or filter rule in the README component table so future me understands the contract.