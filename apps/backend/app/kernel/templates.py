from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any


def _domains_dir() -> Path:
    # app/kernel/templates.py -> app/; then /domains
    return Path(__file__).resolve().parent.parent / "domains"


def _legacy_templates_dir() -> Path:
    # app/templates (legacy fallback)
    return Path(__file__).resolve().parent.parent / "templates"


@lru_cache(maxsize=128)
def _build_env(domain: str | None) -> "jinja2.Environment":  # type: ignore[name-defined]
    import jinja2

    search_paths: list[Path] = []
    domains_dir = _domains_dir()
    # Shared base/partials first
    system_templates = domains_dir / "system" / "templates"
    if system_templates.exists():
        search_paths.append(system_templates)
    # Domain-specific templates
    if domain:
        dpath = domains_dir / domain / "templates"
        if dpath.exists():
            search_paths.append(dpath)
    else:
        # No domain specified: aggregate all domain template dirs
        for child in sorted(domains_dir.iterdir() if domains_dir.exists() else []):
            t = child / "templates"
            if t.exists():
                search_paths.append(t)
    # Legacy fallback (deprecated)
    legacy = _legacy_templates_dir()
    if legacy.exists():
        search_paths.append(legacy)

    loader = jinja2.FileSystemLoader([str(p) for p in search_paths])
    env = jinja2.Environment(
        loader=loader,
        autoescape=jinja2.select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def render(domain: str | None, template_name: str, context: dict[str, Any] | None = None) -> str:
    """Render a template.

    - When ``domain`` is provided, search in ``domains/system/templates`` and
      then in ``domains/<domain>/templates``.
    - When omitted, search all domain templates with system first.
    - As a last resort, also searches legacy ``app/templates`` (deprecated).
    """
    ctx = context or {}
    env = _build_env(domain)
    tpl = env.get_template(template_name)
    return tpl.render(**ctx)


class TemplateService:
    def render_html(self, domain: str, name: str, context: dict[str, Any] | None = None) -> str:
        return render(domain, name, context)

    def render_text(self, domain: str, name: str, context: dict[str, Any] | None = None) -> str:
        return render(domain, name, context)


__all__ = ["TemplateService", "render"]

