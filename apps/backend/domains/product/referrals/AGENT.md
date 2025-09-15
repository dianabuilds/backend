# AGENT — Referrals

Structure: api/, application/, domain/, adapters/.

Rules
- No monolith imports. All logic via ports/adapters (memory here).
- Feature gating happens via DDD Settings (APP_REFERRALS_ENABLED).

API
- /v1/referrals/me/code, /v1/referrals/me/stats
- /v1/admin/referrals/codes*, /events*

