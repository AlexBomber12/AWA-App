from typing import Any, Dict, List


class StrictSpy:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def record(self, **vals: Any) -> None:
        self.calls.append(vals)

    def last(self) -> Dict[str, Any]:
        if not self.calls:
            raise AssertionError("StrictSpy: no calls recorded")
        return self.calls[-1]


__all__ = ["StrictSpy"]
