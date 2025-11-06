from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from services.etl import fba_fee_ingestor, keepa_ingestor, sp_fees


def test_fba_build_idempotency_live() -> None:
    key, meta = fba_fee_ingestor.build_idempotency(True, asins=["A1", "A2"])
    assert key.startswith("b2:")
    assert meta["mode"] == "live"
    assert meta["asin_count"] == 2


def test_fba_fetch_live_fees(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter(
        [
            types.SimpleNamespace(json=lambda: {"totalFbaFee": 1.5}),
            types.SimpleNamespace(json=lambda: {"totalFbaFee": 2.5}),
        ]
    )
    monkeypatch.setattr(fba_fee_ingestor, "http_request", lambda *a, **k: next(responses))
    fees = fba_fee_ingestor.fetch_live_fees(["A1", "A2"], api_key="k", task_id=None)
    assert fees == [("A1", 1.5), ("A2", 2.5)]


def test_keepa_build_idempotency_live(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = types.SimpleNamespace(product_finder=lambda *a, **k: [1, 2, 3])
    monkeypatch.setitem(sys.modules, "keepa", types.SimpleNamespace(Keepa=lambda key: fake_client))
    key, meta = keepa_ingestor.build_idempotency(
        True, fixture_path=Path("x"), offline_output=Path("y")
    )
    assert key.startswith("b2:")
    assert meta["mode"] == "live"


def test_keepa_fetch_live_asins(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {}

    def product_finder(params, domain, n_products):
        called["args"] = (params["sales_rank_lte"], domain, n_products)
        return ["SKU1"]

    fake_client = types.SimpleNamespace(product_finder=product_finder)
    monkeypatch.setitem(sys.modules, "keepa", types.SimpleNamespace(Keepa=lambda key: fake_client))
    result = keepa_ingestor._fetch_live_asins("k", task_id=None)
    assert result == ["SKU1"]
    assert called["args"][1] == "IT"


def test_keepa_build_idempotency_offline(tmp_path: Path) -> None:
    fixture = tmp_path / "sample.json"
    fixture.write_text("[]")
    offline = tmp_path / "output.json"
    key, meta = keepa_ingestor.build_idempotency(
        False, fixture_path=fixture, offline_output=offline
    )
    assert key.startswith("b2:")
    assert meta["mode"] == "offline"
    assert meta["offline_output"] == str(offline)


def test_sp_build_idempotency_live(monkeypatch: pytest.MonkeyPatch) -> None:
    key, meta = sp_fees.build_idempotency(True, skus=["SKU1"], fixture_path=Path("fixture"))
    assert key.startswith("b2:")
    assert meta["mode"] == "live"
    assert meta["sku_count"] == 1


def test_sp_build_rows_from_live(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeAPI:
        def get_my_fees_estimate_for_sku(self, sku):
            return {
                "payload": {
                    "FeesEstimateResult": {"FeesEstimate": {"TotalFeesEstimate": {"Amount": 10.0}}}
                }
            }

    monkeypatch.setitem(
        sys.modules,
        "sp_api.api",
        types.SimpleNamespace(SellingPartnerAPI=lambda **kwargs: FakeAPI()),
    )
    rows = sp_fees.build_rows_from_live(
        ["SKU1"],
        refresh_token="r",
        client_id="c",
        client_secret="s",
        region="US",
    )
    assert rows[0]["amount"] == 10.0
