from __future__ import annotations

import pytest

from services.logistics_etl import client, flow, repository


@pytest.mark.asyncio
async def test_full_idempotent_skips_second_run(monkeypatch):
    batch_calls: list[tuple[str, int, int]] = []
    monkeypatch.setattr(
        flow,
        "record_etl_batch",
        lambda job, processed, errors, duration_s: batch_calls.append((job, processed, errors)),
    )
    retry_calls: list[tuple[str, str]] = []
    monkeypatch.setattr(flow, "record_etl_retry", lambda job, reason: retry_calls.append((job, reason)))

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

    assert len(batch_calls) == 2
    assert batch_calls[0][1] == 1  # processed row count
    assert batch_calls[1][1] == 0  # skipped second run
    assert not retry_calls


@pytest.mark.asyncio
async def test_full_records_failure(monkeypatch):
    retry_calls: list[tuple[str, str]] = []
    monkeypatch.setattr(flow, "record_etl_retry", lambda job, reason: retry_calls.append((job, reason)))
    monkeypatch.setattr(
        flow,
        "record_etl_batch",
        lambda job, processed, errors, duration_s: None,
    )

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

    assert retry_calls == [("logistics_etl", "RuntimeError")]
