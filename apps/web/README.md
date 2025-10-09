Clean React app (`apps/web`) with the ThemeForest template isolated in `apps/web/vendor/template`.

Key rules
- Work only inside `apps/web/src/**` and `apps/web/src/shared/ui/**`.
- Import UI only via `@ui/*`. Direct imports from `vendor` or `ts/demo` are forbidden (ESLint rule).
- Vendor/template code is excluded from TS, ESLint, Prettier, and Vite scanning.

Getting started
1) Install deps:
   npm install

2) Start dev server:
   npm run dev

3) API base URL is configured via `.env.local`:
   VITE_API_BASE=http://127.0.0.1:8000
   VITE_AUTH_ENDPOINT=/v1/auth/login

Linking to backend auth
- Dev: Vite proxy forwards `/v1/**` requests to `VITE_API_BASE` (see `vite.config.ts`), so no extra CORS/OPTIONS plumbing is required.
- Prod: replicate the same proxy rules in the upstream gateway or CDN.
- Authentication endpoint: `POST /v1/auth/login`.
- Login payload: JSON with `email` and `password` fields.
- Requests must use `credentials: 'include'`, because cookies store the auth session.

Moving the existing template
- Preferred (with git):
  PowerShell
    New-Item -ItemType Directory -Force apps/web/vendor | Out-Null
    git mv apps/web/ts/demo apps/web/vendor/template

- Without git:
  PowerShell
    New-Item -ItemType Directory -Force apps/web/vendor | Out-Null
    Move-Item apps/web/ts/demo apps/web/vendor/template

Using components from the template
1) Identify the minimal component code in `apps/web/vendor/template`.
2) Copy only required files into `apps/web/src/shared/ui/<Component>/`.
3) Re-export through `apps/web/src/shared/ui/index.ts`.
4) Import from `@ui/<Component>` in your app.

Workspaces (optional)
If this repo uses npm workspaces at the root, ensure root `package.json` includes:

  {
    "private": true,
    "workspaces": ["apps/web"]
  }

Then you can run from the repo root:

  npm run --workspace apps/web dev

## Checks

```
npm run lint       # ESLint across src
npm run typecheck  # TypeScript project validation
npm run check      # lint + typecheck
```

To run them automatically with backend pre-commit hooks:

```
pre-commit run --all-files --config apps/backend/.pre-commit-config.yaml
```

## UI primitives

- `@ui/Table` provides presets (`base`, `management`, `surface`), helper states (`Table.Empty`, `Table.Error`, `Table.Loading`) and pagination helpers.
- `@ui/PageHero` supports layout modes `default`, `metrics`, `compact` and exposes slots for actions, filters, and metrics in page headers.
- Re-export every shared primitive from `src/shared/ui/index.ts`.

## Storybook

```
npm run storybook       # start the local component catalog
npm run storybook:build # emit static bundle (storybook-static)
```

Document new UI primitives via stories in the `*.stories.tsx` files or MDX docs.

## Visual tests

```
# Set the CHROMATIC_PROJECT_TOKEN secret in .env
npm run visual:test
```

The command publishes Storybook to Chromatic using `--exit-zero-on-changes`. Review snapshots in Chromatic and promote baselines there when they look correct.
