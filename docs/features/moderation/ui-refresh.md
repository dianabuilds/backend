# Moderation UI Refresh Guide

## Scope and Goals
- Align every moderation page with the shared admin visual language.
- Highlight workload hotspots (queues, SLA risk, high risk users) and surface the next action for moderators.
- Standardise loading, empty, and error states so the interface remains trustworthy when data feeds lag.
- Prepare component updates for incremental rollout without breaking existing routes or APIs.

## Foundation
- **Grid and spacing**: use the existing admin grid (8 px). Primary gutters 24 px on desktop, 16 px on tablet. Maintain a 24 px vertical rhythm between sections.
- **Typography**: Inter 600/32 for page titles, 500/18 for section headings, 400/14 for body text, 500/12 for labels and helper copy. Enforce via shared `Text` tokens to avoid mixed weights.
- **Color and elevation**: reuse the neutral scale (`gray-900` to `gray-200`) plus role accents (`emerald` success, `amber` warning, `rose` danger, `violet` primary). Apply shadow level `xl` only for floating cards; default tables use borders instead of shadows.
- **Buttons and links**: `Primary` (solid violet) for the main action per view, `Secondary` (outline) for supporting choices, `Ghost` for refresh/reset. Reserve inline text links for navigation.
- **Icons and chips**: rely on existing `Badge` and `StatusChip` components for statuses, risk levels, and SLA signals. Map everything to the standard semantic colors.
- **Dark mode**: follow the current `@ui` token set so gradients, borders, and backgrounds stay consistent across themes.

## Page Skeleton Patterns
- **Page header / hero**: sticky block (max height 220 px) with title, last refresh timestamp, and up to two KPI cards. Keep the background plain; apply gradients only when a campaign highlight is required.
- **Control bar**: compact row under the hero with search, saved filter chips, auto refresh toggle, and the primary CTA. Allow wrapping on narrow screens.
- **Content area**: default layout uses a two column grid (`2/3` + `1/3`) on viewports >= 1440 px and single column below that breakpoint. Tables receive sticky headers and horizontal scroll if columns overflow.
- **Secondary panels**: drawers and sidebars are 420 px wide on desktop, full width on mobile. Each includes a sticky footer for action buttons.

## Data States
- **Loading**: render skeletons that match the final layout (hero metrics, table rows, timeline cards). Use spinners only for short async actions such as assigning a case.
- **Empty**: pair clear copy with a CTA (`Connect data source`, `Create rule`, `Import template`). Use the illustration set already exposed from `@ui`.
- **Error**: show an inline alert card (rose background) with retry, but keep stale data visible when possible. Also emit a toast for logging.
- **Auto refresh**: display a status string (`Auto refresh - updated 2m ago`) with a colored dot (emerald when healthy, rose on failure) and keep a manual `Refresh` button enabled when not polling.

## Interaction Principles
- Mass actions sit in a sticky footer that appears after any table selection (`Assign`, `Change status`, `Merge`). Disable items that do not apply to the selection.
- Drawer actions (`Assign to me`, `Escalate`, `Resolve`) live in a sticky header. Warn before closing if there are unsaved edits.
- Timeline events carry type chips (`Internal`, `Customer`, `System`), timestamps, and optional pin toggles. New entries drop in at the top with a brief highlight.
- Status or role changes push a toast and append to the history tab automatically.
- Keyboard support: follow visual order for `Tab`, and keep `Ctrl/Cmd + Enter` for submitting notes. `Esc` closes drawers.

## Page Specific Guidelines

### Overview (`/moderation/overview`)
- KPI cards: `Queues backlog`, `Incidents (24h)`, `SLA avg response`, `AI automation share`. Give helper text that references the top queue or missing data.
- Replace the loose action-card grid with grouped blocks: `Queues health` (sortable list with SLA badge and quick link), `Incidents` (recent escalations), `Operational trends` (chart area with loading and error states), `Recent sanctions` (list with moderator attribution).
- Empty analytics state: dashed outline card that explains the missing feed and offers `Connect analytics feed`.
- Hero actions include `Refresh`, `Manage sources`, and the auto refresh status indicator.

### Cases (`/moderation/cases`)
- Control bar: combined search (ID, title, subject), saved filter chips, toggle `My cases`, dropdown `Auto refresh`. Provide `Save filter` and `Clear`.
- Table columns: `ID`, `Title`, `Queue`, `Severity`, `Priority`, `SLA` (countdown chip), `Assignee`, `Updated`. Use semantic badge colors for status and SLA risk (green on track, amber at risk, red breached).
- Add unread badge and hover quick actions (`Assign`, `Resolve`). Bulk selection opens footer actions `Assign owner`, `Change status`, `Merge`, `Export` with success toasts.

### Case Detail
- Drawer and standalone page share structure: left column timeline, right column tabs `Workflow`, `Details`, `History`.
- `Workflow` tab: status picker, severity, priority, queue selector, SLA card with trend. Provide contextual helper copy such as "No queue selected - choose routing".
- `Details` tab: editable form for title, subject, description, tags with validation messages. Sticky footer hosts `Save changes`, `Mark resolved`, `Move to escalation`.
- `History` tab: chronological audit log with actor, timestamp, summary, and filters for event types.
- Timeline cards display color coded headers, attachments, mentions, and optional pin toggles. The `Add internal note` composer sits below the list.

### Users (`/moderation/users`)
- Hero cards cover `High risk`, `Under sanctions`, `New complaints`. Keep `Create case` as a prominent button on the right.
- Filters: status select, role select, risk chips, search (email, username, ID). Offer an `Advanced filters` modal for compound criteria.
- Table columns: `User`, `Role`, `Status`, `Risk`, `Complaints`, `Sanctions`, `Last seen`, `Actions`. Risk chip color reflects severity; sanctions column shows active count or `None`.
- Side panel width 420 px with tabs `Overview`, `Roles`, `Sanctions`, `Notes`, `Activity`. Each tab includes helper text and a sticky action footer (`Update roles`, `Apply sanction`, `Save note`).
- `Sanctions` tab uses presets for duration, requires reason, and previews impact. `Activity` tab lists tickets and reports with a `Refresh activity` control.

### AI Rules (`/moderation/ai-rules`)
- Hero: summary metrics for `Total`, `Enabled`, `Disabled`, `Errors` plus primary CTA `Create rule` and secondary `Import template`.
- Rule list: rows or cards with `Category`, `Trigger`, `Threshold`, `Default action`, `Updated`, `Owner`, `Status`. Quick actions include `Enable/Disable`, `Edit`, `Diagnostics`.
- Empty state: onboarding checklist (connect data source, create rule, test sample) and a `Load demo dataset` button.
- Creation flow: four step wizard `Category -> Conditions -> Action -> Test`, with live preview of sample input and predicted outcome.

## Implementation Notes
- Ship updated tokens and components through the shared UI kit (`@ui`) before touching feature pages: hero variant, control bar, sticky footer, timeline card, KPI chip.
- Confirm required fields with backend before removing placeholders. Handle `loading`, `empty`, and `error` states explicitly in each API hook.
- Cover critical flows with integration tests (table selection, bulk actions, drawer forms, rule wizard).
- Schedule a moderator usability check after the first implementation pass to validate priority signals and action placement.
