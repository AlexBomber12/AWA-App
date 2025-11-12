from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from services.price_importer.io import iter_price_batches


@pytest.mark.asyncio
async def test_iter_price_batches_streams_csv(tmp_path):
    csv_path = tmp_path / "vendor.csv"
    csv_path.write_text("sku,cost,currency\nSKU-1,10,eur\nSKU-2,5,usd\n", encoding="utf-8")

    batches: list[list[dict[str, object]]] = []
    async for batch in iter_price_batches(csv_path, batch_size=1, max_workers=1):
        batches.append(batch)
    assert len(batches) == 2
    assert batches[0][0]["currency"] == "EUR"


@pytest.mark.asyncio
async def test_iter_price_batches_ignores_empty_frames(monkeypatch):
    from services.price_importer import io

    def fake_frame_iterator(_path, _batch_size):
        df_empty = pd.DataFrame(columns=["sku", "cost", "currency"])
        df_full = pd.DataFrame([{"sku": "A", "cost": 1, "currency": "EUR"}])

        def _gen():
            yield df_empty
            yield df_full

        return _gen()

    monkeypatch.setattr(io, "_frame_iterator", fake_frame_iterator, raising=False)
    monkeypatch.setattr(io, "detect_format", lambda *_a, **_kw: "csv", raising=False)

    batches: list[list[dict[str, object]]] = []
    async for batch in io.iter_price_batches(Path("dummy.csv"), batch_size=1, max_workers=1):
        batches.append(batch)
    assert len(batches) == 1
    assert batches[0][0]["sku"] == "A"
