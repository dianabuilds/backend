Shared Module Guidelines (for Agents and Developers)

Purpose
- `app/shared` is the single place for universal, side‑effect‑free helpers that
  any domain can import.

Rules
- Side‑effect‑free: no HTTP/DB/file I/O, no network, no environment mutation.
- No imports from `app.domains.*` or `app.providers.*`.
- Allowed deps: stdlib, typing, dataclasses, pydantic (and similar pure libs),
  and select primitives from `app.kernel` that are also pure.

What to put here
- Value objects, small validators, pure helper functions, lightweight mixins,
  protocol/type definitions used across multiple domains.

What not to put here
- Infrastructure adapters, settings loaders, HTTP clients, DB code.
- Domain‑specific contracts or implementations.

Migration from `app/common`
- Move implementation into `app/shared`.
- Keep `app/common/<module>.py` as a thin re‑export with a DeprecationWarning.
- Replace imports across the codebase to `app.shared.<module>`.
- Delete `app/common` once no imports remain.

Linting/Contracts
- Import Linter is configured to forbid `app.common` usage (with transitional
  allowances for the `app.shared` shims). New code must import from `app.shared`.

