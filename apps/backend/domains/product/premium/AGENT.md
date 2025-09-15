# AGENT — Premium

Structure: api/, application/.

Rules
- No monolith imports; service computes plan and quota status in-memory.
- Router gated by APP_PREMIUM_ENABLED.

API
- /v1/premium/me/limits

