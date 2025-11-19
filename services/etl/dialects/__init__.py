from __future__ import annotations

import re
from collections.abc import Iterable

from awa_common.settings import settings

_WS = re.compile(r"\s+")


def normalise_headers(cols: Iterable[str]) -> list[str]:
    return [_WS.sub(" ", c.strip().lower()) for c in cols]


if getattr(getattr(settings, "app", None), "testing", getattr(settings, "TESTING", False)):
    from . import test_generic  # noqa: F401
