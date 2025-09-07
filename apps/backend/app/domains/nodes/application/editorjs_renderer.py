from __future__ import annotations

"""Minimal server-side renderer for EditorJS content.

The admin UI can use this pre-rendered HTML for preview to avoid
client-side handling of every possible block type. The renderer
supports a safe subset of blocks (header, paragraph, list, image, quote)
and ignores unknown types.
"""

from html import escape
from typing import Any


SUPPORTED_BLOCKS = {"header", "paragraph", "list", "image", "quote"}


def _render_header(data: dict[str, Any]) -> str:
    level = int(data.get("level") or 2)
    level = 1 if level < 1 else 6 if level > 6 else level
    text = data.get("text") or ""
    return f"<h{level}>{text}</h{level}>"


def _render_paragraph(data: dict[str, Any]) -> str:
    text = data.get("text") or ""
    return f"<p>{text}</p>"


def _render_list(data: dict[str, Any]) -> str:
    items = data.get("items") or []
    if not isinstance(items, list):
        return ""
    style = (data.get("style") or "unordered").lower()
    tag = "ol" if style == "ordered" else "ul"
    rendered = "".join(f"<li>{escape(str(i))}</li>" for i in items)
    return f"<{tag}>{rendered}</{tag}>"


def _render_image(data: dict[str, Any]) -> str:
    # EditorJS image tool uses data.file.url
    file = data.get("file") or {}
    url = file.get("url") or data.get("url") or ""
    cap = data.get("caption") or ""
    if not url:
        return ""
    return f'<figure><img src="{escape(str(url))}" alt="{escape(str(cap))}">{f"<figcaption>{escape(str(cap))}</figcaption>" if cap else ""}</figure>'


def _render_quote(data: dict[str, Any]) -> str:
    txt = data.get("text") or ""
    cap = data.get("caption") or ""
    cap_html = f"<cite>{escape(str(cap))}</cite>" if cap else ""
    return f"<blockquote>{txt}{cap_html}</blockquote>"


def render_html(content: Any) -> str:
    """Render EditorJS content (dict with blocks) to HTML string.

    Unknown blocks are skipped. Rendering does not sanitize embedded
    HTML inside text fields – the admin preview is trusted; for public
    rendering employ a sanitizer upstream if required.
    """
    try:
        blocks = []
        if isinstance(content, dict):
            blocks = content.get("blocks") or []
        elif isinstance(content, str):
            import json

            obj = json.loads(content)
            if isinstance(obj, dict):
                blocks = obj.get("blocks") or []
        html_parts: list[str] = []
        for b in blocks or []:
            btype = (b or {}).get("type")
            data = (b or {}).get("data") or {}
            if btype == "header":
                html_parts.append(_render_header(data))
            elif btype == "paragraph":
                html_parts.append(_render_paragraph(data))
            elif btype == "list":
                html_parts.append(_render_list(data))
            elif btype == "image":
                html_parts.append(_render_image(data))
            elif btype == "quote":
                html_parts.append(_render_quote(data))
            else:
                # skip unknown
                continue
        return "".join(html_parts)
    except Exception:
        return ""


def collect_unknown_blocks(content: Any) -> list[str]:
    """Return list of unique unsupported block types in the document."""
    seen: set[str] = set()
    try:
        blocks = []
        if isinstance(content, dict):
            blocks = content.get("blocks") or []
        elif isinstance(content, str):
            import json

            obj = json.loads(content)
            if isinstance(obj, dict):
                blocks = obj.get("blocks") or []
        for b in blocks or []:
            t = (b or {}).get("type")
            if t and t not in SUPPORTED_BLOCKS:
                seen.add(str(t))
    except Exception:
        pass
    return sorted(seen)

