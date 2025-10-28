# Playbook биллинга (EVM)

Документ описывает порядок вывода биллинга с EVM-провайдером в прод и реакцию на основные инциденты. Используйте совместно со схемой архитектуры (`docs/features/billing/blueprint.md`) и таск-листом (`docs/features/billing/tasks.md`).

## 1. Предрелизная подготовка
- **Миграции**: убедитесь, что применены `001_billing.sql`, `002_contracts.sql`, `003_crypto_config.sql`.
- **Конфигурация**: заданы переменные `BILLING_EVM_GATEWAYS`, `BILLING_RPC_CONFIG`, `BILLING_WEBHOOK_SECRET`, `APP_BILLING_FINANCE_OPS_USER_ID`.
- **Контракты**: зарегистрированы on-chain адреса, ABI и методы `mint`/`burn`. Проверьте, что секрет вебхука совпадает с релеем.
- **Quota/Notifications/Audit**: схемы событий `billing.plan.changed.v1`, шаблоны уведомлений и источники аудита подключены.
- **Дашборды**: в Grafana опубликованы панели `Billing Overview` (Prometheus) и дашборды по Quota.

## 2. Проверка перед выкладкой
1. Заполните `.env` или секреты окружения нужными переменными.
2. Выполните скрипт E2E:
   ```bash
   python apps/backend/scripts/billing_e2e.py --user-id <uuid> --rpc-url <rpc> --webhook-secret <secret>
   ```
   Скрипт создаст демонстрационный план, выполнит checkout → webhook и распечатает:
   - чек-аут payload для кошелька;
   - запись в ledger;
   - опубликованные события, уведомления и записи аудита;
   - bundle пользователя (wallet, задолженность, история).
3. Убедитесь, что в `/v1/billing/overview/*` появились данные (минимум pending-платёж).
4. Запустите smoke-тесты: `python -m pytest tests/smoke/test_api_billing.py`.

## 3. Rollout
- **Blue/Green**: выводите по контурам (staging → canary → prod). На каждом этапе прогоняйте E2E-скрипт.
- **Workers**: включите `billing.contracts_listener` и убедитесь, что он подключился к RPC.
- **Finance Ops**: оповестите команду о новых маршрутах `/v1/billing/overview/*` и роли `finance_ops`.
- **Feature Flags**: при необходимости ограничьте доступ к EVM-планам через gateway конфиг (enabled=false).

## 4. Мониторинг и алерты
- Метрики `billing_transactions_total`, `billing_subscriptions_active`, `billing_transactions_network_failed_total`, `billing_contract_events_total`.
- Логи с контекстом `tx_hash`, `user_id`, `contract_slug`; трассы в OTLP.
- Базовые алерты:
  - <5 успешных подтверждений за 15 минут.
  - Рост `failed` платежей >10% (rolling 30m).
  - Задержка webhook > 2 минут (`confirmed_at` - `created_at`).
  - RPC ошибки > 5% за 5 минут.

## 5. Типовые инциденты
### 5.1. Webhook не приходит / HMAC не совпадает
1. Сверьте `webhook_secret` в контракте и секрет релея.
2. Проверьте логи `billing.contracts_listener` — при успехе он повторно отправит событие.
3. При необходимости выполните `POST /v1/billing/contracts/webhook` вручную с корректной подписью.

### 5.2. Ledger расходитcя с on-chain
1. Используйте `/v1/billing/overview/payouts?status=pending` для выявления зависших транзакций.
2. Запустите фоновые ретраи: `python -m domains.platform.billing.workers.contracts_listener --reconcile`.
3. При критическом расхождении вручную обновите запись в `payment_transactions` и отправьте уведомление ops.

### 5.3. Пользователь жалуется на отказ оплаты
1. Выполните `/v1/billing/overview/users/{user_id}/history` и `/summary`.
2. Проверьте события в `packages/events` (топик `billing.plan.changed.v1`) — должен быть статус `failed`.
3. Сообщите пользователю причины (`failure_reason`) и предложите повторить checkout. При системной ошибке — эскалируйте в infra.

### 5.4. RPC недоступен
1. Алерт сработает по росту ошибок. Переключите `crypto_config` на запасной RPC:
   ```bash
   curl -X POST /v1/billing/overview/crypto-config \
        -H "Authorization: Bearer <token>" \
        -d '{"rpc_endpoints": {"<network>": "<backup_rpc>"}}'
   ```
2. Убедитесь, что воркер снова обрабатывает события.
3. Зафиксируйте инцидент в audit + уведомите finance_ops.

## 6. Пост-инцидентный анализ
- Снимите экспорт метрик, журналов и трасс.
- В `docs/features/billing/tasks.md` добавьте follow-up (например, улучшение ретраев или алертов).
- Обновите плейбук, если обнаружен новый сценарий.

## 7. Полезные команды
- **E2E локально**: `python apps/backend/scripts/billing_e2e.py --rpc-url http://localhost:8545`.
- **Очистка демо-данных**: удалите план и контракт через admin API (`DELETE /v1/billing/admin/plans/{slug}`).
- **Просмотр метрик**: `curl http://localhost:8000/v1/metrics | grep billing_`.

## 8. Контакты
- Finance Ops: `#finops-billing`
- On-call инженер: см. `docs/playbooks/notifications.md`
- Инфраструктура RPC: `#infra-blockchain`

