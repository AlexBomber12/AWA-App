from typing import Any


class StrictSpy:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def record(self, **vals: Any) -> None:
        self.calls.append(vals)

    def last(self) -> dict[str, Any]:
        if not self.calls:
            raise AssertionError("StrictSpy: no calls recorded")
        return self.calls[-1]


__all__ = ["StrictSpy"]
