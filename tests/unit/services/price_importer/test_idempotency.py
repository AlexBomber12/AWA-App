from __future__ import annotations

import argparse
import asyncio
import importlib
from pathlib import Path

import pytest

price_import = importlib.import_module("services.price_importer.import")


class _StubSession:
    def __init__(self) -> None:
        self.executed: list[tuple] = []
        self.closed = False

    def execute(self, stmt, params=None):
        self.executed.append((stmt, params))

    def commit(self):
        return None

    def rollback(self):
        return None

    def close(self):
        self.closed = True


class DummyRepo:
    def __init__(self) -> None:
        self.engine = object()

    def ensure_vendor(self, name: str) -> int:
        return 42

    def upsert_prices(self, vendor_id: int, batch, dry_run: bool = False) -> tuple[int, int]:
        return len(batch), 0


async def _fake_batches(_path: str, batch_size: int = 10):
    yield [{"sku": "SKU1", "unit_price": 1.0, "currency": "EUR"}]


async def _bad_batches(_path: str, batch_size: int = 10):
    raise ValueError("bad input")


def _sts(tmp_path: Path) -> argparse.Namespace:
    csv = tmp_path / "prices.csv"
    csv.write_text("sku,cost\nA,1.00\n")
    return argparse.Namespace(file=str(csv), vendor="ACME", dry_run=False, batch_size=10)


def test_price_import_idempotent_skip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, stub_load_log) -> None:
    args = _sts(tmp_path)
    monkeypatch.setattr(price_import, "Repository", DummyRepo)
    monkeypatch.setattr(price_import, "iter_price_batches", _fake_batches)
    monkeypatch.setattr(price_import, "sessionmaker", lambda *a, **k: (lambda: _StubSession()))

    asyncio.run(price_import._run_import(args))
    first_status = {record["status"] for record in stub_load_log.values()}
    assert "success" in first_status

    asyncio.run(price_import._run_import(args))
    statuses = {record["status"] for record in stub_load_log.values()}
    assert "skipped" in statuses


def test_price_import_error_marks_failed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, stub_load_log) -> None:
    args = _sts(tmp_path)
    monkeypatch.setattr(price_import, "Repository", DummyRepo)
    monkeypatch.setattr(price_import, "iter_price_batches", _bad_batches)
    monkeypatch.setattr(price_import, "sessionmaker", lambda *a, **k: (lambda: _StubSession()))

    with pytest.raises(ValueError):
        asyncio.run(price_import._run_import(args))
    statuses = {record["status"] for record in stub_load_log.values()}
    assert "failed" in statuses
