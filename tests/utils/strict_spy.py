from __future__ import annotations

from typing import Any


class StrictSpy:
    """Simple structured spy that records all call payloads."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def record(self, **vals: Any) -> None:
        self.calls.append(dict(vals))

    def last(self) -> dict[str, Any]:
        if not self.calls:
            raise AssertionError("StrictSpy: no calls recorded")
        return self.calls[-1]


__all__ = ["StrictSpy"]
