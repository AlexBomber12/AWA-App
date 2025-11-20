from __future__ import annotations

from datetime import datetime
from typing import Any

class croniter:
    expanded: list[list[Any]]

    def __init__(
        self, expr: str, start_time: Any | None = ..., ret_type: Any | None = ..., day_or: bool = ...
    ) -> None: ...
    def get_next(self, ret_type: Any | None = ...) -> Any: ...
    @staticmethod
    def match(expr: str, dt: datetime) -> bool: ...
