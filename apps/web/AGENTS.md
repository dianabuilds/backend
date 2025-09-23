Frontend Agent Guide (apps/web)

Purpose
- Build the product UI using ONLY the template’s design system and iconography. Keep minimal custom code, isolate template sources, and preserve a clean app.

Directories
- app code: `apps/web/src`
  - `layout/` — shell (Sidebar, Topbar, AppLayout)
  - `pages/<feature>/` — page components (route targets)
  - `shared/ui/` — curated UI wrappers using template classes (single import surface `@ui`)
  - `shared/icons/` — curated icon exports from Heroicons (single import surface `@icons`)
  - `shared/api/` — API client helpers (`apiGet`, `apiPost`, `apiPut`)
  - `shared/auth/` — auth context (login/logout, me)
  - `styles/` — app styles entry importing template CSS
- vendor template (do not modify/use directly from app): `apps/web/vendor/template/**`

Styling & Components (must follow)
- Use template CSS only:
  - Global CSS is imported in `src/styles/index.css` from `vendor/template/src/styles/index.css` (Tailwind v4 + layers).
  - NO custom design systems or third‑party UI kits.
- Components:
  - Import UI ONLY from `@ui` (i.e. `src/shared/ui`).
  - Добавлять новые компоненты так: `src/shared/ui/<Component>/index.tsx` (обёртка над классами темы или минимальный перенос из vendor), публичный экспорт — через `src/shared/ui/index.ts`.
  - Нельзя импортировать напрямую из `vendor/template/src/**` в коде приложения.
- Icons:
  - Импорт иконок ТОЛЬКО из `src/shared/icons` (курируемый реэкспорт Heroicons). Если какой‑то иконки не хватает — добавь её в `shared/icons/index.ts`.
  - Запрещены внешние наборы иконок (react-icons, lucide, fontawesome и т.п.).

Routing & Layout
- Хост‑разметка и навигация живут в `src/layout/*`. Страницы — в `src/pages/<feature>/<Page>.tsx`.
- Новые роуты регистрируй в `src/App.tsx`. Защищённые — оборачивать в `RequireAuth`.

API & Авторизация
- Используй только `shared/api/client.ts`:
  - `apiGet`, `apiPost`, `apiPut` автоматически подставляют Authorization Bearer и CSRF‑заголовок из cookie.
  - В dev все вызовы должны быть относительными (`/v1/...`) — их проксирует Vite (см. `vite.config.ts`).
- Логин/логаут и состояние пользователя — через `shared/auth/AuthContext`.

Выравнивание по бэкенду
- Добавляй фичи только под существующие ручки API. Проверка:
  - Список подключённых роутеров: `apps/backend/app/api_gateway/main.py`.
  - Примеры доступных ручек: `/v1/auth/*`, `/v1/users/me`, `/v1/notifications`, `/v1/billing/*`, `/v1/search/*`.
- Если ручек нет (например, соц. авторизация) — UI не добавляем.

Код‑правила
- Компонентные импорты: только `@ui/*`. Иконки: только `@icons`.
- Стили: классы темы (Tailwind v4 utilities + CSS layers). Inline‑style допускаются только для мелких вычислимых значений; выносите в классы перед мерджем.
- Типы/TS: строгий режим включён. Не отключать без причины. Не добавлять any без необходимости.
- Никаких прямых импортов из `vendor/*` и внешних UI/иконок — ESLint это запрещает.

ESLint/Prettier/Typecheck
- Lint: `npm run lint` (flat config, запреты импортов включены)
- Типы: `npm run typecheck`
- Сборка: `npm run build`

Как перенести компонент из шаблона правильно
1) Найди минимально нужные куски разметки/логики в `vendor/template/src/components/**`.
2) Создай `src/shared/ui/<Component>/index.tsx` и перенеси только необходимое; используй классы темы.
3) Экспортируй через `src/shared/ui/index.ts`.
4) Импорты в страницах — только `@ui/<Component>`.

Assets
- Если понадобятся изображения из шаблона — копируй в `apps/web/public/images/...` (не подключать vendor/public напрямую). Ссылки вида `/images/...` раздаются Vite из `public/`.

PR‑чеклист
- [ ] Нет импортов из запрещённых путей (vendor, сторонние UI/иконки).
- [ ] Все UI‑импорты из `@ui`, все иконки — из `@icons`.
- [ ] Страница/фича опирается только на существующие API‑ручки.
- [ ] `npm run typecheck` и `npm run lint` — без ошибок.
