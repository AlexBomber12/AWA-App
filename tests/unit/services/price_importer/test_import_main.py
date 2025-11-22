from __future__ import annotations

import importlib
from decimal import Decimal
from types import SimpleNamespace

import pytest


def _get_importer_module():
    return importlib.import_module("services.price_importer.import")


def test_main_processes_batches(monkeypatch, tmp_path):
    importer = _get_importer_module()
    tmp_file = tmp_path / "prices.csv"
    tmp_file.write_text("unused", encoding="utf-8")

    batches = [
        [{"sku": "A1", "unit_price": Decimal("1"), "currency": "EUR", "moq": 0, "lead_time_d": 0}],
        [{"sku": "A2", "unit_price": Decimal("2"), "currency": "USD", "moq": 1, "lead_time_d": 5}],
    ]

    async def _fake_batches(*_a, **_k):
        for batch in batches:
            yield batch

    monkeypatch.setattr(importer, "_bootstrap_observability", lambda: None, raising=False)
    monkeypatch.setattr(importer, "iter_price_batches", _fake_batches, raising=False)

    class DummyRepo:
        def ensure_vendor(self, vendor: str) -> int:
            assert vendor == "ACME"
            return 1

        def upsert_prices(self, vendor_id, batch, dry_run=False):
            return len(batch), 0

    events: list[str] = []
    monkeypatch.setattr(importer, "Repository", lambda: DummyRepo(), raising=False)
    monkeypatch.setattr(
        importer,
        "logger",
        SimpleNamespace(
            info=lambda event, **kwargs: events.append(event), error=lambda *a, **k: events.append("error")
        ),
        raising=False,
    )

    exit_code = importer.main([str(tmp_file), "--vendor", "ACME"])
    assert exit_code == 0
    assert "price_import.completed" in events


def test_main_logs_validation_errors(monkeypatch, tmp_path):
    importer = _get_importer_module()

    tmp_file = tmp_path / "prices.csv"
    tmp_file.write_text("unused", encoding="utf-8")

    async def _failing_batches(*_a, **_k):
        raise ValueError("invalid")
        if False:  # pragma: no cover - ensure async generator semantics
            yield []

    monkeypatch.setattr(importer, "_bootstrap_observability", lambda: None, raising=False)
    monkeypatch.setattr(importer, "iter_price_batches", _failing_batches, raising=False)

    captured = []
    monkeypatch.setattr(
        importer,
        "logger",
        SimpleNamespace(info=lambda *a, **k: None, error=lambda event, **kw: captured.append((event, kw))),
        raising=False,
    )

    class DummyRepo:
        def ensure_vendor(self, vendor: str) -> int:
            return 7

    monkeypatch.setattr(importer, "Repository", lambda: DummyRepo(), raising=False)

    with pytest.raises(ValueError):
        importer.main([str(tmp_file), "--vendor", "ACME"])

    assert captured and captured[0][0] == "price_import.validation_failed"


def test_merge_mappings_and_safe_value():
    importer = _get_importer_module()
    llm_result = importer.PriceListLLMResult(
        detected_columns={"vendor_sku": "SKU", "unit_price": "Price"},
        column_confidence={"vendor_sku": 0.9, "unit_price": 0.2},
    )
    merged = importer._merge_mappings({"vendor_sku": "guess"}, llm_result, min_confidence=0.5)
    assert merged["vendor_sku"] == "SKU"
    assert "unit_price" not in merged  # confidence too low keeps heuristic
    assert importer._safe_value(None) is None
    assert importer._safe_value({"x": 1}) == "{'x': 1}"
