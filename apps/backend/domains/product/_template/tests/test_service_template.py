from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="template only; copy and adapt in a real domain")


def test_template_exists() -> None:
    assert True
