from __future__ import annotations

from collections.abc import Iterable
from typing import Any

try:
    from prometheus_client import Counter as _Counter, Summary as _Summary
except Exception:  # pragma: no cover - exercised when optional deps missing

    class _NoopMetricChild:
        def __init__(self, parent: _NoopMetric, key: tuple[Any, ...], kind: str) -> None:
            self._parent = parent
            self._key = key
            self._kind = kind

        def inc(self, amount: float = 1.0) -> None:
            if self._kind != "counter":
                return
            current = self._parent._values.get(self._key, 0.0)
            self._parent._values[self._key] = current + amount

        def observe(self, value: float) -> None:
            if self._kind != "summary":
                return
            bucket = self._parent._values.setdefault(self._key, [])
            bucket.append(value)

    class _NoopMetric:
        def __init__(self, name: str, documentation: str, labelnames: Iterable[str], kind: str) -> None:
            self._name = name
            self._documentation = documentation
            self._labelnames = tuple(labelnames)
            self._kind = kind
            self._values: dict[tuple[Any, ...], Any] = {}

        def labels(self, *values: Any, **kwargs: Any) -> _NoopMetricChild:
            if kwargs:
                key = tuple(kwargs[label] for label in self._labelnames)
            else:
                if len(values) != len(self._labelnames):
                    raise ValueError("Label cardinality mismatch")
                key = tuple(values)
            return _NoopMetricChild(self, key, self._kind)

    def _Counter(name: str, documentation: str, labelnames: Iterable[str]):  # type: ignore
        return _NoopMetric(name, documentation, labelnames, "counter")

    def _Summary(name: str, documentation: str, labelnames: Iterable[str]):  # type: ignore
        return _NoopMetric(name, documentation, labelnames, "summary")


etl_runs_total = _Counter("etl_runs_total", "ETL runs", ["source", "status"])
etl_failures_total = _Counter("etl_failures_total", "ETL failures", ["source", "reason"])
etl_latency_seconds = _Summary("etl_latency_seconds", "ETL latency", ["source"])
