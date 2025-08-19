from __future__ import annotations

import os
import re
from collections.abc import Iterable

_WS = re.compile(r"\s+")


def normalise_headers(cols: Iterable[str]) -> list[str]:
    return [_WS.sub(" ", c.strip().lower()) for c in cols]


if os.getenv("TESTING") == "1":
    from . import test_generic  # noqa: F401
