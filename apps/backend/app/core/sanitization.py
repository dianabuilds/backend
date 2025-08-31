import re
from collections.abc import Iterable

# Пытаемся использовать bleach, если установлен
try:
    import bleach  # type: ignore
except Exception:  # bleach не установлен — используем фолбэк
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

DEFAULT_ATTRS = {
    "*": ["class", "id", "title", "aria-label"],
    "a": ["href", "name", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "span": ["style"],
}
DEFAULT_PROTOCOLS = ["http", "https", "mailto", "tel", "data"]


def sanitize_html(
    html: str,
    tags: Iterable[str] = DEFAULT_TAGS,
    attrs: dict[str, Iterable[str]] = DEFAULT_ATTRS,
    protocols: Iterable[str] = DEFAULT_PROTOCOLS,
) -> str:
    """
    Очищает HTML от опасного содержимого (XSS).
    Если доступен bleach — использует его. Иначе — фолбэк-очистка.
    """
    if not html:
        return html

    if bleach:
        # Убираем потенциально опасные атрибуты/схемы
        cleaned = bleach.clean(
            html,
            tags=list(tags),
            attributes={k: list(v) for k, v in attrs.items()},
            protocols=list(protocols),
            strip=True,
        )
        # Гарантируем безопасные ссылки
        cleaned = bleach.linkify(
            cleaned,
            callbacks=[bleach.linkifier.DEFAULT_CALLBACKS],
            skip_tags=["pre", "code"],
        )
        return cleaned

    # Фолбэк: вырезаем script/iframe и опасные схемы/обработчики событий.
    cleaned = re.sub(
        r"(?is)<\s*(script|iframe|object|embed|style)[^>]*>.*?<\s*/\s*\1\s*>", "", html
    )
    # Удаляем on* обработчики
    cleaned = re.sub(r"(?i)\son\w+\s*=\s*(['\"]).*?\1", "", cleaned)
    # Запрещаем javascript: и data: в href/src
    cleaned = re.sub(
        r'(?i)\s(href|src)\s*=\s*([\'"])\s*(javascript:|data:)(.*?)\2', r"", cleaned
    )
    return cleaned
