# Архитектурный дизайн и маршрутизация контуров API

- **Статус:** Draft  
- **Дата:** 2025-10-19  
- **Связанные документы:** `docs/adr-api-segmentation.md`, `docs/api-inventory/access-policy.md`, `docs/api-inventory/endpoints.md`

Документ описывает сетевое разделение, маршрутизацию и паттерн деплоя для публичного, административного и операционного контуров. Он служит исходной точкой для согласования с DevOps и безопасностью, а затем станет основой для реализации Terraform/Helm-карт.

## 1. Цели и ограничения

- Гарантировать, что клиенты публичного сайта не имеют сетевого доступа к административным и операционным сервисам.
- Обеспечить отдельные цепочки деплоя и масштабирования для `public`, `admin`, `ops`, уменьшить blast radius релизов.
- Сохранить единый контроль аутентификации (IdP) и наблюдаемости, но с раздельной сегрегацией трафика и логов.
- Учитывать существующий набор маршрутов (260 шт., `docs/api-inventory/endpoints.md`) и роль-модель (`docs/api-inventory/access-policy.md`).

## 2. Сетевая топология

### 2.1 Зоны и подсети

| Зона | Назначение | Пример сегмента (CIDR) | Комментарии |
|------|------------|------------------------|-------------|
| **Edge / WAF** | Приём трафика из интернета, DDoS/WAF фильтрация | `10.0.0.0/26` | Cloud LB + WAF (AWS ALB/WAF, Cloudflare, т.п.) |
| **DMZ-public** | Ингресс и сервисы публичного контура | `10.0.0.64/26` | Разрешён исходящий доступ к IdP, CDN, публичным API |
| **DMZ-admin** | Ингресс админки, модерации, telemetry dashboards | `10.0.0.128/26` | Доступ только через VPN/Zero Trust |
| **DMZ-ops** | Ингресс для биллинга, внутренних операторов | `10.0.0.192/26` | Требуется MFA, IP allowlist, дополнительные IDS |
| **Service Core** | Backend-сервисы (FastAPI, workers), event bus | `10.0.1.0/24` | Подразделяется namespace-ами |
| **Data** | Базы данных, Redis, blob | `10.0.2.0/24` | Доступ только из Service Core и ops workers |

### 2.2 Kubernetes/Service Mesh разбиение

- Один кластер Kubernetes с namespaces:  
  - `app-public`, `app-admin`, `app-ops` — ingress + gateway + API pods.  
  - `core-services` — доменные сервисы (nodes, billing, notifications).  
  - `shared-infra` — observability, message bus, redis.  
- NetworkPolicy/ServiceMesh (Istio/Linkerd) применяются для ограничения East-West трафика.  
- Для критичных частей (billing, ops) допускается отдельный кластер (multi-cluster) — фиксируется дополнительным ADR при необходимости.

## 3. DNS и маршрутизация

| Audience | DNS/Ingress | Хост | Путь | Target namespace/service |
|----------|-------------|------|------|--------------------------|
| Public | `public.api.example.com` | `public.api.example.com` | `/v1/*`, `/healthz` | `app-public/backend-gateway` |
| Admin | `admin.api.example.com` | `admin.api.example.com` | `/v1/admin/*`, `/api/moderation/*`, `/v1/telemetry/*` | `app-admin/backend-gateway` |
| Ops | `ops.api.example.com` | `ops.api.example.com` | `/v1/billing/*`, `/v1/notifications/admin/*`, `/v1/quota/*` | `app-ops/backend-gateway` |
| Services | `*.svc.cluster.local` | — | gRPC/internal HTTP | Service mesh routing |

Все ingress-хосты защищены TLS (Let’s Encrypt/ACM). Для админки и ops дополнительно используются mTLS от клиента (через Zero Trust proxy).

### 3.1 Пример маршрутизации (Envoy Gateway)

```yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: public-api
  namespace: app-public
spec:
  parentRefs:
    - name: public-gateway
  hostnames:
    - public.api.example.com
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /v1/
      filters:
        - type: RequestHeaderModifier
          requestHeaderModifier:
            set:
              - name: X-Audience
                value: public
      backendRefs:
        - name: backend-api
          port: 8080
    - matches:
        - path:
            type: PathPrefix
            value: /healthz
      backendRefs:
        - name: health-probe
          port: 8081
```

Аналогичные маршруты создаются для admin/ops, но с отдельными gateway (ingress) объектами, обязательными фильтрами (проверка mTLS, JWT, rate-limit).

## 4. Firewall и IAM-политики

| Источник → Назначение | Разрешено | Условия |
|-----------------------|-----------|---------|
| Edge → DMZ-public | Да | TCP/443, WAF правила OWASP, rate-limit |
| Edge → DMZ-admin/ops | Да | Только после VPN/Zero Trust, mTLS, IP allowlist |
| DMZ-public → Service Core | Да | HTTP/HTTPS к `public-backend` сервисам, NetworkPolicy `audience=public` |
| DMZ-admin → Service Core | Да | HTTP/HTTPS + mTLS к сервисам с label `audience in {admin, shared}` |
| DMZ-ops → Service Core | Да | HTTP/HTTPS + mTLS к сервисам `audience in {ops, shared}`, отдельный сервис-аккаунт |
| DMZ-* → Data | Нет | Только через Service Core; прямой доступ запрещён |
| Service Core → Data | Да | По списку портов (Postgres 5432, Redis 6379), с ограничением по namespace |
| Service Core ↔ Observability | Да | gRPC/OTLP с mutual TLS |

Чекпоинты:
- Каждые 6 месяцев — аудит Security Group/Firewall правил.
- Alert при попытке обращения audience `public` к маршруту admin/ops (подключение к SIEM).

## 5. Паттерн деплоя и балансировки

- Публичный контур масштабируется по метрикам RPS/CPU; admin и ops — ручное масштабирование с верхним пределом.
- Canary/blue-green релизы проводятся отдельно по ingress: `public-canary.api.example.com` и т.д.
- Stateful сервисы (Postgres, Redis) размещаются в приватной подсети с управляемыми сервисами (RDS/Cloud SQL); доступ через IAM роли.
- Выпуск сертификатов автоматизирован (cert-manager). Ротация TLS ≤ 60 дней.
- `app-admin` и `app-ops` используют отдельные service accounts и PodSecurityPolicies, запрещающие доступ к hostPath/privileged.

## 6. Конфигурация логирования и наблюдаемости

- Все gateway пишут access-логи в отдельные потоки (`public-access`, `admin-access`, `ops-access`).
- Tracing/metrics проходят через общий OTEL Collector в `shared-infra`, но с атрибутом `audience`.  
  Настройка фильтров/квот — `apps/backend/infra/observability/`.
- Security события (403, попытки доступа) отправляются в SIEM, создаются дежурные алерты.

## 7. План внедрения

1. **Подготовительный этап:** разместить ingress-контроллеры и namespaces, применить NetworkPolicy (можно без разреза трафика).  
2. **Миграция публичного контура:** перенастроить DNS на `public.api`, протестировать, затем включить WAF.  
3. **Миграция админки и ops:** завести Zero Trust/VPN, настроить mTLS, переключить фронтенды на новые хосты.  
4. **Данные и сервисы:** сегментировать доступ к БД, внедрить role-based service accounts, ограничить admin API ключи.  
5. **Контроль:** добавить проверки в CI (policy-as-code) и регулярные PenTest.

## 8. Открытые вопросы

- Нужно утвердить конкретных провайдеров (Cloudflare vs. AWS WAF) и возможности для mTLS.
- Вопрос multi-region: при появлении второго региона потребуется расширение схемы (global load balancer + geo-DNS).
- Сервисная сеть (Service Mesh) — требуется PoC для Istio/Linkerd, чтобы не усложнить латентность публичных запросов.

После согласования документ будет переведён из Draft в Accepted и дополнен Terraform/Helm шаблонами.
