from __future__ import annotations

import os
from typing import Optional

from .openai import OpenAIProvider


class OpenAICompatibleProvider(OpenAIProvider):
    """Provider for OpenAI-Compatible APIs.

    This provider behaves like :class:`OpenAIProvider` but reads credentials
    and base URL from ``OPENAI_COMPATIBLE_*`` environment variables by
    default. It can be used with any service exposing the OpenAI REST
    interface (e.g. open-source or self-hosted models).
    """

    name = "openai_compatible"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(
            api_key=api_key
            or os.getenv("OPENAI_COMPATIBLE_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or "",
            base_url=(
                base_url
                or os.getenv("OPENAI_COMPATIBLE_BASE_URL")
                or os.getenv("OPENAI_BASE_URL")
                or "https://api.openai.com"
            ),
        )
