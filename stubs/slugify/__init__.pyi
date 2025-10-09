from typing import Any, Sequence, Tuple

def slugify(
    text: str,
    *,
    lowercase: bool = ...,
    separator: str = ...,
    allow_unicode: bool = ...,
    replacements: Sequence[Tuple[str, str]] | None = ...,
    **kwargs: Any
) -> str: ...
