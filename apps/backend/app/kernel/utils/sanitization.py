from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

# Try to use bleach if available; otherwise provide a safe fallback
try:
    import bleach  # type: ignore
except Exception:  # bleach not installed — fallback sanitizer
    bleach = None  # type: ignore


DEFAULT_TAGS = [
    "a",
    "abbr",
    "b",
    "blockquote",
    "br",
    "code",
    "em",
    "i",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "ul",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "span",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
]

DEFAULT_ATTRS: Mapping[str, Iterable[str]] = {
    "*": ["class", "id", "title", "aria-label"],
    "a": ["href", "name", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "span": ["style"],
}
DEFAULT_PROTOCOLS = ["http", "https", "mailto", "tel", "data"]


def sanitize_html(
    html: str,
    tags: Iterable[str] = DEFAULT_TAGS,
    attrs: Mapping[str, Iterable[str]] | None = None,
    protocols: Iterable[str] = DEFAULT_PROTOCOLS,
) -> str:
    """Clean HTML from dangerous content (XSS).

    Uses bleach when available; otherwise applies a conservative regex cleanup.
    """
    if not html:
        return html

    if attrs is None:
        attrs = DEFAULT_ATTRS

    if bleach:
        cleaned = bleach.clean(
            html,
            tags=list(tags),
            attributes={k: list(v) for k, v in attrs.items()},
            protocols=list(protocols),
            strip=True,
        )
        cleaned = bleach.linkify(
            cleaned,
            callbacks=[bleach.linkifier.DEFAULT_CALLBACKS],
            skip_tags=["pre", "code"],
        )
        return cleaned

    # Fallback: strip script/iframe and dangerous attributes/schemes
    cleaned = re.sub(
        r"(?is)<\s*(script|iframe|object|embed|style)[^>]*>.*?<\s*/\s*\1\s*>", "", html
    )
    cleaned = re.sub(r"(?i)\son\w+\s*=\s*(['\"]).*?\1", "", cleaned)
    cleaned = re.sub(r"(?i)\s(href|src)\s*=\s*(['\"])\s*(javascript:|data:)(.*?)\2", r"", cleaned)
    return cleaned


__all__ = ["sanitize_html", "DEFAULT_TAGS", "DEFAULT_ATTRS", "DEFAULT_PROTOCOLS"]

