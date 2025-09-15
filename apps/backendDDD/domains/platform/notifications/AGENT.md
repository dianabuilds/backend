# AGENT — Notifications

Где править:
- Диспетчер: `logic/dispatcher.py` (`register_channel`, `dispatch` с retry)
- Каналы: `adapters/email_smtp.py`, `adapters/webhook.py`
- API: `api/http.py` (`POST /v1/notifications/send`)
- Проводка: `wires.py` (регистрация каналов и подписка на темы через Events)

Правила:
- Канал `email` использует SMTP, в mock‑режиме логирует, в проде — шлёт письма.
- Канал `webhook` отправляет JSON, заголовки/секреты можно добавить в адаптере.
- Admin‑guard + CSRF на `/send`.

