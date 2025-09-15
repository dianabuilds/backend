# Platform Telemetry — Domain Overview

Назначение: сбор и экспозиция технических метрик (Prometheus‑совместимые), RUM‑события из фронтенда, а также вспомогательные журналы (аудит, этапы генераций) через порты.

Компоненты
- Порты: `ports/*` (RUM, Audit, Generation, RawPayload, LLM sink).
- Приложение: `application/*` (сервисы и ин‑мемори хранилища метрик).
- Адаптеры: `adapters/rum_repository.py`, `adapters/llm_metrics_adapter.py`.
- API: `api/http.py` (`/v1/metrics`, `/v1/metrics/rum`), `api/admin_http.py` (`/v1/admin/telemetry/rum*`).
- Проводка: `wires.py` — сборка RUM‑репозитория и сервиса.

Контракты
- Формат RUM‑события: `{ event: str, ts: int, url: str, data?: object }`.
- `/v1/metrics` — текст в формате Prometheus exposition.

Настройки
- Берутся из `packages/core/config.py` (используется `redis_url`).

