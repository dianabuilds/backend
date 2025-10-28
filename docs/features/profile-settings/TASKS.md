# Backlog – Profile Settings Improvements

Each task should result in a PR referenced from this list. Order is indicative; tackle
blocking items first.

## P0 – Critical Gaps

1. ~~**Wire admin/public routers**~~ ✅ (2025‑10‑28)  
   - Реализованы реальные хендлеры в `domains.product.profile.api.admin/public`.  
   - Gateway подключает их по контурам; добавлены интеграционные и contour-тесты (`tests/integration/test_profile_routes.py`, `tests/app/api_gateway/test_contours.py`).  
   - Документация обновлена: `docs/features/profile-settings/README.md`.

2. **Provide event schemas**  
   - Add JSON Schemas for `profile.email.change.requested.v1`, `profile.email.updated.v1`,
     `profile.wallet.updated.v1`, and `profile.wallet.cleared.v1`.  
   - Extend tests to validate payloads against the registry.  
   - Update documentation describing event fields.

3. **API integration tests**  
   - Create FastAPI test suite for settings routes (`/v1/me/settings/profile` and
     `/v1/settings/profile/{user_id}`).  
   - Cover success paths, ETag enforcement, error mapping, CSRF/idempotency requirements,
     and wallet/email workflows.

## P1 – Functional Enhancements

4. **Align rate limit payload**  
   - Adjust `profile_payload` augmentation so settings responses expose profile-relevant
     limits (username/email cooldown info) rather than global public rate limits.  
   - Update clients and documentation accordingly.

5. **Wallet signature handling**  
   - Normalise chain IDs, verify optional signatures, and persist verification metadata.  
   - Introduce feature flag gating if external verification service is required.

6. **Flags dependency audit**  
   - Either leverage `Flags` inside `Service` (e.g., to toggle wallet verification logic)
     or remove the unused dependency to simplify wiring.

## P2 – Quality & Observability

7. **Audit logging for admin actions**  
   - Emit structured audit events when admins update profiles or manage wallets/emails.  
   - Ensure records link to acting admin and affected user.

8. **Metrics coverage**  
   - Implement latency metrics for email confirm/request and wallet operations.  
   - Wire them into the metrics registry and document SLO expectations.

9. **Documentation upkeep**  
   - Cross-link this feature doc from the top-level `docs/README.md` and the profile
     domain docs.  
   - Keep diagrams or flow descriptions in sync once routers go live.
