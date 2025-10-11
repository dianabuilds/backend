# Отчёт по зависимостям фронтенда (2025-10-11)

## Инструмент и запуск
- Источник данных — `apps/web/src`, результаты сохраняются в `var/frontend-deps`.

## Матрица слоёв
| Из слоя \ В слой | shared | features | pages | layout | internal |
|------------------|--------|----------|-------|--------|----------|
| layout           | 7      | 0        | 0     | 2      | 0        |
| pages            | 165    | 27       | 102   | 0      | 1        |
| features         | 208    | 179      | 0     | 0      | 0        |
| shared           | 235    | 0        | 0     | 0      | 0        |

## Нарушения
- Нарушений слоёв не обнаружено (0 импортов `features → pages`).

## Прочие наблюдения
- Импортов из `vendor/*` не обнаружено.
- Один нерешённый импорт — `src/main.tsx` → `./styles/index.css`; CSS не анализируется скриптом и исключён из отчёта.

## Артефакты
- `var/frontend-deps/dependency-edges.json` — полный список импортов (990 связей).
- `var/frontend-deps/layer-matrix.json` — агрегированная матрица по слоям.
- `var/frontend-deps/violations.json` — перечень нарушений с деталями.

## Автоматизация
- Быстрая проверка: `npm run lint:deps` (запускает `scripts/analyze-frontend-deps.mjs --check` без перезаписи отчётов).
- Полное обновление артефактов: `node scripts/analyze-frontend-deps.mjs`.
