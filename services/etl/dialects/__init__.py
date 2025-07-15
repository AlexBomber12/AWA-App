from __future__ import annotations

from collections.abc import Iterable


def normalise_headers(cols: Iterable[str]) -> list[str]:
    return [c.lower().strip() for c in cols]
