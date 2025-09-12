Shared (app/shared)

Purpose
- Host universally reusable, side‑effect‑free utilities shared across domains.
- Make import boundaries explicit: domains may import from shared, but shared
  must never import from domains.

What belongs here
- Pure helpers and abstractions: e.g., value objects, validation helpers,
  simple dataclasses or Pydantic models without I/O.
- Small mixins or base classes that do not perform I/O at import time.
- Lightweight type aliases and protocol definitions (when not domain‑specific).

What does NOT belong here
- Any infrastructure or I/O code (HTTP clients, DB sessions, filesystem, etc.).
- Domain‑specific contracts (keep inside each domain’s package) unless explicitly
  promoted to a cross‑domain contract.
- Anything importing from ``app.domains.*``, ``app.providers.*``, or code with
  side effects at import time.

Allowed dependencies
- Python stdlib, typing, dataclasses.
- Pydantic and other pure‑functionality libraries (no global I/O on import).
- ``app.kernel`` ONLY for constants or very basic primitives that are also
  side‑effect‑free.

Prohibited dependencies
- ``app.domains.*`` (any domain layer)
- ``app.providers.*`` and infrastructure adapters
- Direct HTTP/DB/file I/O or environment mutation

Import policy
- Domains can import from: ``app/kernel``, ``app/shared``, and themselves.
- ``app/shared`` must never import from domains; keep acyclic.

Review checklist (before adding code here)
- Is this generic enough to be useful across multiple domains?
- Is there any I/O or global state at import time? If yes, do not place here.
- Does it import from domains or providers? If yes, refactor or move elsewhere.
- Is there a domain where this fits better? Prefer locality over over‑sharing.

Migration tips
- When moving from ``app/common`` to ``app/shared``, prefer moving implementations
  into ``app/shared`` and keep thin re‑exports in ``app/common`` with a
  DeprecationWarning until imports are replaced. Then delete ``app/common``.

