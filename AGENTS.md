# agents.md — спецификация поведения ИИ-агента для репозитория

> Единый источник правды о том, **как агент генерирует и меняет код** в нашем проекте. Распространяется на бэкенд (
> Python/FastAPI, PostgreSQL, Redis), фронтенд (Next.js/TypeScript, Tailwind), инфраструктуру (CI/CD, Docker, IaC) и
> документацию. Любые отступления — только через `WAIVER`.

## Общие требования

* Перед коммитом запускать `pre-commit run --files <изменённые файлы>`.
* Прогонять тесты по затронутым компонентам: бэкенд `pytest`, фронтенд `pnpm test`.
* Если проверки выполнить невозможно, агент обязан явно сообщить об этом в отчёте.

## 1. Архитектура проекта (контекст)

* **Бэкенд**: Python ≥ 3.11, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, PostgreSQL 15, Redis 7. Фичи: квесты/пещеры,
  переходы между нодами (manual/conditional/echo/compass/random), премиум-гейтинг, уведомления по тегам, backend-driven
  UI (сервер отдаёт JSON-схемы экранов с bindings, vars, условиями, действиями, аналитикой и версионированием).
* **Фронтенд (web/mob-web)**: Next.js (App Router) + TypeScript, Tailwind, shadcn/ui, React Query; PWA для моб-веб;
  SSR/SSG для SEO. Компоненты домена: `QuestCard`, `CompassPanel`, `NodeMap`, `EchoList`, `TrailPath`,
  `AchievementBadge`, `PremiumWall`, `NotifPrefs`, `AIQuestWizard`.
* **Инфраструктура**: Docker, GitHub Actions, Renovate, SonarCloud/SonarQube, SBOM (CycloneDX). Наблюдаемость:
  структурные логи, метрики и трассировки.

## 2. Базовые принципы

* **План → Тесты → Код → Самопроверка → PR**. Код без тестов и самоаудита запрещён.
* **Малые инкременты**: один смысл — один PR. Feature flags для поведения.
* **Безопасность и производительность по умолчанию**. Бюджеты фиксированы, регресс без `WAIVER` блокируется.
* **Документация — часть Definition of Done**: README/ADR/миграции/схемы API.

## 3. Рабочий поток агента

1. **<PLAN>**: краткая стратегия (≤ 200 слов), затронутые модули, риски.
2. **<TESTS>**: юнит/проперти/контракты, фикстуры и baseline покрытия.
3. **<CODE>**: реализация только в рамках соглашений и слоёв.
4. **<SELF-REVIEW>**: чек-лист, результаты линтеров/тайпов, покрытие, бенчмарки, лицензии, SBOM.
5. **PR**: шаблон заполнен полностью, прикреплены артефакты.

## 4. Слои и границы

* Слои бэка: `api` → `service` → `domain` → `repo` (SQLAlchemy) → `infra`.
* Слои фронта: `app/` → `widgets/` → `features/` → `entities/` → `shared/`.
* **Запрещено**: бизнес-логика в контроллерах, «скрытый I/O» в домене, кросс-доменные зависимости без портов/фасадов.

## 5. Стиль и инструменты

### Python

* **black**, **ruff** (с isort), **mypy --strict**, **bandit**, **vulture**, **pip-audit**.
* `from __future__ import annotations` обязателен.

### TypeScript/Next.js

* **eslint**, **prettier**, strict TypeScript.
* Тесты: **Vitest** + Testing Library, E2E: **Playwright**.
* Стили: Tailwind, shadcn/ui.

### Infra

* Docker: **hadolint**, CI: **actionlint**, IaC: **tfsec**/`checkov`.
* Secrets: **gitleaks**, лицензии: Sonar/`license-checker`.

## 6. Тестовая стратегия

* Юнит-тесты: `pytest`/`vitest`.
* Property-based: `hypothesis`.
* Контрактные: Pact.
* Интеграционные: Testcontainers (pg, redis).
* Мутационное: `mutmut` / `stryker`, score ≥ 60 %.
* E2E smoke: Playwright.
* Покрытие: backend ≥ 80 %, frontend ≥ 70 %.

## 7. Бюджеты производительности

* API: P95 < 120 ms, P99 < 300 ms.
* Фронтенд: LCP < 2.5 s, TBT < 150 ms, CLS < 0.1.
* Backend-driven UI: схема < 60 KB, генерация < 80 ms.
* Регресс > 10 % без `WAIVER` блокирует merge.

## 8. Зависимости

Не больше 2 новых на PR, каждую обосновывать. Renovate для обновлений.

## 9. Безопасность

SAST (Sonar), фаззинг для парсеров, SBOM (CycloneDX), secrets-scan.

## 10. Наблюдаемость

Логи через адаптер (`trace_id`, `user_id?`, `plan_id?`, `premium_tier?`). Метрики + трассировки.

## 11. Definition of Done

Все линтеры/тайпы зелёные, покрытие не ниже baseline, перф в норме, доки обновлены.

## 12. Шаблон PR

```
Title: <scope>: <short intent>
Summary: что меняем и зачем
Design: архитектурный подход, альтернативы
Risks: регрессы, миграции
Tests: список тестов + coverage deltas
Perf: бенчмарки до/после
Security: выводы SAST, лицензии
Docs: какие разделы обновлены
WAIVER?: правило, причина, срок, владелец
```

## 13. Контракт промпта для агента

Формат:

```
<PLAN>...</PLAN>
<TESTS>...</TESTS>
<CODE>...</CODE>
<SELF-REVIEW>...</SELF-REVIEW>
```

Запрещено без `<TESTS>` и `<SELF-REVIEW>`.

Чек-лист: тесты зелёные, линтеры зелёные, перф ок, зависимости допустимы, ADR/схемы обновлены.

## 14. Backend-driven UI

Версионирование схем, `premiumLevel`, `visibleIf`, `quotaKey`, analytics только с сервера.

## 15. Примеры/анти-примеры

* ✅ Малый PR: компонент + схема + тесты + перф в норме.
* ❌ Плохой PR: лишняя зависимость, бизнес-логика в контроллере, тестов нет.

## 16. Исключения (`WAIVER`)

```
<WAIVER>
rule: performance.api.p95
reason: временный регресс
expires: 2025-10-15
owner: @team/backend
mitigation: новый индекс
</WAIVER>
```

## 17. CI/CD

Этапы: lint/types → unit → property/contracts → integration → e2e smoke → security → quality (Sonar, SBOM) →
benchmarks → release.

## 18. Локальные команды

`make ql`, `make test`, `make bench`. pre-commit обязателен.

## 19. ADR и документация

ADR в `docs/adr/`, схемы API/UI с версионированием.

## 20. Подпись коммитов

Conventional Commits, semver, auto-changelog. Коммиты агента подписаны.

---

**TL;DR:** агент всегда идёт по циклу план → тесты → код → самоаудит → PR. Любой регресс без `WAIVER` — блок.
