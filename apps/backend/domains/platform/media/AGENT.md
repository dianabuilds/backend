# AGENT — Media

Где править:
- Сторедж: `adapters/local_storage.py` (шардирование директорий, пути)
- Сервис: `application/storage_service.py`
- API: `api/http.py` — загрузка/выдача
- DI: `wires.py`

Правила:
- Хранить в `var/uploads/xx/yy/<uuid>.<ext>`; URL `/v1/media/file/xx/yy/<name>`.
- Ограничения: типы (jpeg/png/webp), размер ≤5MB, защита от traversal.

