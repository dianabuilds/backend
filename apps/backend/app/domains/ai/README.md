# AI (Генерация квестов)

Цель: собрать все части, относящиеся к генерации ИИ-контента, в один модуль.

План миграции (эволюционно):
- pipeline: перенос `app/services/ai_generation_pipeline.py` → `app/domains/ai/pipeline.py`
- persist: перенос `app/services/ai_generation_persist.py` → `app/domains/ai/persist.py`
- providers: перенос `app/services/llm_providers/*` → `app/domains/ai/providers/*`
- logs: перенос `app/models/ai_generation_log.py` + сервис сохранения → `app/domains/ai/logs.py`
- worker: перенос `app/engine/ai_worker.py` → `app/domains/ai/worker.py`
- api (admin): агрегация роутеров AI под `app/domains/ai/api.py`

Контракты не меняем; импорты переключим после переноса.
