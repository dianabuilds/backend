# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

## API clients

The admin UI talks to the backend using two helpers:

- `profileApi` — sets common headers and appends the selected profile ID as the `profile_id` query parameter. Pass the profile ID explicitly to every call: `profileApi.get('/admin/…', { profileId })`. To skip automatic query injection, use `{ profile: false }`.
- `accountApi` — legacy helper kept for backward compatibility during transition. Prefer `profileApi` for all new code.
- `api` — thin wrapper around `fetch` without account handling. Use it for public or auth routes.

## Hotkeys

- `⌘K` / `Ctrl+K` — open the command palette for quick navigation to **Status**, **Limits** and **Trace** pages.
- `Esc` — close the command palette.

## Status and Flags

Admin tables separate workflow **Status** from boolean **Flags**.

### Status

The **Status** column is read-only and reflects the backend's `workflow.status` field:

- 📝 **Draft**
- 🔍 **In review**
- ✅ **Published**
- 🗄️ **Archived**

### Flags

The **Flags** column groups toggleable icons. Clicking an icon sends a `PATCH` request to flip the corresponding field and updates the row on success:

- 💎 **Premium** – gated for paying users.
- ⭐ **Recommendable** – eligible for recommendations.
- 👁️ / 🚫 **Visibility** – controls whether the item is visible.

### Icon legend

| Icon | Meaning |
| ---- | ------- |
| 📝 | Draft |
| 🔍 | In review |
| ✅ | Published |
| 🗄️ | Archived |
| 💎 | Premium flag |
| ⭐ | Recommendable flag |
| 👁️ / 🚫 | Visible / hidden |

## UI components

### Tooltip

Form fields use a shared `Tooltip` component to show brief explanations on hover.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      ...tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      ...tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      ...tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
