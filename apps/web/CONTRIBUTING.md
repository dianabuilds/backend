# Frontend Contribution Guide

## Storybook & Visual Tests
- Keep new UI primitives documented in Storybook. Run `npm run storybook` locally to review states before opening a PR.
- Visual regression pipeline uses Chromatic. To validate locally set `CHROMATIC_PROJECT_TOKEN` in `.env` and run `npm run visual:test` after `npm run storybook:build` finishes.
- Always add at least one story per variant (states, loading, error). For complex flows attach short MDX guidance alongside stories.

## Component Patterns
- Reuse shared primitives: `@ui/Table` (presets + actions + state rows) and `@ui/PageHero` for page headers. Do not inline bespoke table or hero markup.
- Prefer composition: pass actions/filters/metrics via slots instead of hard-coded layout.
- Keep page headers below 420px height (default). Override `maxHeight` thoughtfully.

## Code Style
- Use TypeScript strict mode; never disable lint rules without justification. Run `npm run lint` and `npm run test` before pushing.
- New helpers belong in `shared/utils/format.ts` with corresponding unit tests in `format.test.ts`.
- Snapshot/visual diffs must be reviewed in Chromatic before merge.