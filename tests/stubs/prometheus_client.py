from __future__ import annotations

import contextlib
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any

CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"


class CollectorRegistry:
    def __init__(self) -> None:
        self._metrics: list[_BaseMetric] = []

    def register(self, metric: _BaseMetric) -> None:
        if metric not in self._metrics:
            self._metrics.append(metric)

    def collect(self) -> Iterator[_BaseMetric]:
        yield from list(self._metrics)


_DEFAULT_REGISTRY = CollectorRegistry()


@dataclass
class _Sample:
    name: str
    labels: dict[str, str]
    value: float


class _MetricFamily:
    def __init__(self, name: str, documentation: str, typ: str) -> None:
        self.name = name
        self.documentation = documentation
        self.type = typ
        self.samples: list[_Sample] = []


class _BaseMetric:
    prom_type = "untyped"

    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.documentation = documentation
        self.labelnames = tuple(labelnames or ())
        self._values: dict[tuple[str, ...], dict[str, Any]] = {}
        self._kwargs = dict(kwargs)
        registry: CollectorRegistry | None = self._kwargs.pop("registry", None)
        self._registry = registry or _DEFAULT_REGISTRY
        self._registry.register(self)

    def clear(self) -> None:
        self._values.clear()

    def labels(self, *values: Any, **kwargs: Any) -> _MetricChild:
        if kwargs:
            key = tuple(str(kwargs[label]) for label in self.labelnames)
        else:
            key = tuple(str(v) for v in values)
        if len(key) != len(self.labelnames):
            raise ValueError("Label cardinality mismatch")
        return _MetricChild(self, key)

    def collect(self) -> list[_MetricFamily]:
        family = _MetricFamily(self.name, self.documentation, self.prom_type)
        family.samples.extend(self._collect_samples())
        return [family]

    def _ensure_entry(self, key: tuple[str, ...]) -> dict[str, Any]:
        return self._values.setdefault(key, {})

    def _inc(self, key: tuple[str, ...], amount: float = 1.0) -> None:
        entry = self._ensure_entry(key)
        entry["value"] = float(entry.get("value", 0.0) + amount)

    def _dec(self, key: tuple[str, ...], amount: float = 1.0) -> None:
        entry = self._ensure_entry(key)
        entry["value"] = float(entry.get("value", 0.0) - amount)

    def _observe(self, key: tuple[str, ...], value: float) -> None:
        entry = self._ensure_entry(key)
        observations = entry.setdefault("observations", [])
        observations.append(float(value))

    def _set(self, key: tuple[str, ...], value: float) -> None:
        entry = self._ensure_entry(key)
        entry["value"] = float(value)

    def _collect_samples(self) -> list[_Sample]:
        samples: list[_Sample] = []
        for key, entry in self._values.items():
            labels = dict(zip(self.labelnames, key, strict=False))
            samples.append(_Sample(self.name, labels, float(entry.get("value", 0.0))))
        return samples

    @contextlib.contextmanager
    def track_inprogress(self) -> Iterator[_MetricChild]:
        child = self.labels(*(None for _ in self.labelnames))
        child.inc()
        try:
            yield child
        finally:
            child.dec()

    @contextlib.contextmanager
    def time(self) -> Iterator[_MetricChild]:
        child = self.labels(*(None for _ in self.labelnames))
        yield child


class Counter(_BaseMetric):
    prom_type = "counter"

    def _collect_samples(self) -> list[_Sample]:
        samples: list[_Sample] = []
        for key, entry in self._values.items():
            labels = dict(zip(self.labelnames, key, strict=False))
            value = float(entry.get("value", 0.0))
            samples.append(_Sample(self.name, labels, value))
            samples.append(_Sample(f"{self.name}_total", labels, value))
        return samples


class Gauge(_BaseMetric):
    prom_type = "gauge"

    def dec(self, amount: float = 1.0) -> None:
        child = self.labels(*(None for _ in self.labelnames))
        child.dec(amount)


class Histogram(_BaseMetric):
    prom_type = "histogram"

    def __init__(
        self,
        name: str,
        documentation: str,
        labelnames: Iterable[str] | None = None,
        **kwargs: Any,
    ) -> None:  # noqa: D401
        super().__init__(name, documentation, labelnames, **kwargs)
        buckets = kwargs.get("buckets")
        if isinstance(buckets, Iterable):
            self.buckets = [float(b) for b in buckets]
        else:
            self.buckets = [0.5, 1.0, 2.5, 5.0]

    def _collect_samples(self) -> list[_Sample]:
        samples: list[_Sample] = []
        for key, entry in self._values.items():
            labels = dict(zip(self.labelnames, key, strict=False))
            observations: list[float] = entry.get("observations", [])
            total = float(sum(observations))
            count = float(len(observations))
            samples.append(_Sample(f"{self.name}_count", labels, count))
            samples.append(_Sample(f"{self.name}_sum", labels, total))
            for bucket in self.buckets:
                bucket_labels = labels.copy()
                bucket_labels["le"] = str(bucket)
                bucket_count = float(sum(1 for value in observations if value <= bucket))
                samples.append(_Sample(f"{self.name}_bucket", bucket_labels, bucket_count))
            bucket_labels = labels.copy()
            bucket_labels["le"] = "+Inf"
            samples.append(_Sample(f"{self.name}_bucket", bucket_labels, count))
        return samples


class Summary(_BaseMetric):
    prom_type = "summary"

    def _collect_samples(self) -> list[_Sample]:
        samples: list[_Sample] = []
        for key, entry in self._values.items():
            labels = dict(zip(self.labelnames, key, strict=False))
            observations: list[float] = entry.get("observations", [])
            total = float(sum(observations))
            count = float(len(observations))
            samples.append(_Sample(f"{self.name}_count", labels, count))
            samples.append(_Sample(f"{self.name}_sum", labels, total))
        return samples


def generate_latest(registry: CollectorRegistry | None = None, *_args: Any, **_kwargs: Any) -> bytes:
    lines: list[str] = []
    reg = registry or _DEFAULT_REGISTRY
    for metric in reg.collect():
        lines.append(f"# HELP {metric.name} {metric.documentation}")
        lines.append(f"# TYPE {metric.name} {metric.prom_type}")
        for sample in metric._collect_samples():
            if sample.labels:
                label_str = ",".join(f'{k}="{v}"' for k, v in sample.labels.items())
                lines.append(f"{sample.name}{{{label_str}}} {sample.value}")
            else:
                lines.append(f"{sample.name} {sample.value}")
    return "\n".join(lines).encode()


def start_http_server(*_args: Any, **_kwargs: Any) -> None:
    return None


class _MetricChild:
    def __init__(self, parent: _BaseMetric, key: tuple[str, ...]) -> None:
        self._parent = parent
        self._key = key

    def inc(self, amount: float = 1.0) -> None:
        self._parent._inc(self._key, amount)

    def observe(self, value: float) -> None:
        self._parent._observe(self._key, value)

    def set(self, value: float) -> None:
        self._parent._set(self._key, value)

    def dec(self, amount: float = 1.0) -> None:
        self._parent._dec(self._key, amount)
