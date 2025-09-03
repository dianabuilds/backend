# Telemetry

Назначение: сбор и экспорт метрик (HTTP/LLM/worker), RUM и сводки.
RUM-события сохраняются в Redis и агрегируются сервисом для `/admin/telemetry/rum/summary`.
