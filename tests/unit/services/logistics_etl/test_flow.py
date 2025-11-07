from __future__ import annotations

from collections import defaultdict
from typing import Any

import pytest

from services.logistics_etl import client, flow, metrics, repository


class _DummyMetricChild:
    def __init__(self, parent: _DummyMetric, key: tuple[tuple[str, Any], ...]) -> None:
        self._parent = parent
        self._key = key

    def inc(self, amount: float = 1.0) -> None:
        self._parent._counters[self._key] += amount

    def observe(self, value: float) -> None:
        self._parent._observations[self._key].append(value)


class _DummyMetric:
    def __init__(self) -> None:
        self._counters: dict[tuple[tuple[str, Any], ...], float] = defaultdict(float)
        self._observations: dict[tuple[tuple[str, Any], ...], list[float]] = defaultdict(list)

    def labels(self, **labels: Any) -> _DummyMetricChild:
        key = tuple(sorted(labels.items()))
        return _DummyMetricChild(self, key)


@pytest.mark.asyncio
async def test_full_idempotent_skips_second_run(monkeypatch):
    runs_metric = _DummyMetric()
    failures_metric = _DummyMetric()
    latency_metric = _DummyMetric()

    monkeypatch.setattr(metrics, "etl_runs_total", runs_metric)
    monkeypatch.setattr(metrics, "etl_failures_total", failures_metric)
    monkeypatch.setattr(metrics, "etl_latency_seconds", latency_metric)

    snapshot = {
        "source": "http://example.com/rates.csv",
        "raw": b"sample-bytes",
        "meta": {"seqno": "v1"},
        "rows": [
            {
                "carrier": "DHL",
                "origin": "DE",
                "dest": "FR",
                "service": "Express",
                "eur_per_kg": 1.25,
                "effective_from": "2024-01-01",
                "effective_to": None,
                "source": "http://example.com/rates.csv",
            }
        ],
        "error": None,
    }

    async def fake_fetch_sources():
        return [snapshot]

    seen_pairs: set[tuple[str, str]] = set()

    async def fake_seen(source: str, sha256: str | None, seqno: str | None) -> bool:
        keys = []
        if sha256:
            keys.append((source, sha256))
        if seqno:
            keys.append((source, seqno))
        return any(key in seen_pairs for key in keys)

    async def fake_mark(source: str, sha256: str | None, seqno: str | None, rows: int) -> None:
        if sha256:
            seen_pairs.add((source, sha256))
        if seqno:
            seen_pairs.add((source, seqno or ""))

    upserts = {"count": 0}

    async def fake_upsert_many(**kwargs):
        upserts["count"] += 1
        return {"inserted": len(kwargs["rows"]), "updated": 0, "skipped": 0}

    monkeypatch.setattr(client, "fetch_sources", fake_fetch_sources)
    monkeypatch.setattr(repository, "seen_load", fake_seen)
    monkeypatch.setattr(repository, "mark_load", fake_mark)
    monkeypatch.setattr(repository, "upsert_many", fake_upsert_many)

    first = await flow.full()
    assert first[0]["skipped"] is False
    assert first[0]["rows_upserted"] == 1
    assert upserts["count"] == 1

    second = await flow.full()
    assert second[0]["skipped"] is True
    assert second[0]["rows_upserted"] == 0
    assert upserts["count"] == 1

    success_key = tuple(sorted([("source", snapshot["source"]), ("status", "success")]))
    skipped_key = tuple(sorted([("source", snapshot["source"]), ("status", "skipped")]))
    assert runs_metric._counters[success_key] >= 1
    assert runs_metric._counters[skipped_key] >= 1
    assert not failures_metric._counters  # no failures reported
    assert latency_metric._observations  # latency recorded


@pytest.mark.asyncio
async def test_full_records_failure(monkeypatch):
    runs_metric = _DummyMetric()
    failures_metric = _DummyMetric()
    latency_metric = _DummyMetric()

    monkeypatch.setattr(metrics, "etl_runs_total", runs_metric)
    monkeypatch.setattr(metrics, "etl_failures_total", failures_metric)
    monkeypatch.setattr(metrics, "etl_latency_seconds", latency_metric)

    async def fake_fetch_sources():
        return [
            {
                "source": "http://example.com/bad.csv",
                "raw": b"",
                "meta": {},
                "rows": [],
                "error": RuntimeError("boom"),
            }
        ]

    async def never_called(*args, **kwargs):
        raise AssertionError("repository function should not be called on failure")

    monkeypatch.setattr(client, "fetch_sources", fake_fetch_sources)
    monkeypatch.setattr(repository, "seen_load", never_called)
    monkeypatch.setattr(repository, "mark_load", never_called)
    monkeypatch.setattr(repository, "upsert_many", never_called)

    results = await flow.full()
    entry = results[0]
    assert entry["rows_upserted"] == 0
    assert entry["skipped"] is False

    failure_key = tuple(sorted([("source", "http://example.com/bad.csv"), ("reason", "RuntimeError")]))
    status_key = tuple(sorted([("source", "http://example.com/bad.csv"), ("status", "failure")]))
    assert failures_metric._counters[failure_key] == 1
    assert runs_metric._counters[status_key] == 1
    assert latency_metric._observations
