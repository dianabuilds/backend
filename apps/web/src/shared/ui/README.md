UI layer usage

- Import UI only from this directory via alias `@ui`.
- Each new component should be a thin wrapper over template classes or a minimal copy from vendor sources.
- Do not import from vendor/template directly in pages/components.
- Keep props small and typed; prefer composition over configuration.

