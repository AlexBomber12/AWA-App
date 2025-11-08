from __future__ import annotations

from pathlib import Path

import pandas as pd

from services.price_importer.io import PriceRow, iter_price_batches


def test_iter_price_batches_streams_csv(tmp_path):
    csv_path = tmp_path / "vendor.csv"
    csv_path.write_text("sku,cost,currency\nSKU-1,10,eur\nSKU-2,5,usd\n", encoding="utf-8")

    batches = list(iter_price_batches(csv_path, batch_size=1))
    assert len(batches) == 2
    assert isinstance(batches[0][0], PriceRow)
    assert batches[0][0].currency == "EUR"


def test_iter_price_batches_ignores_empty_frames(monkeypatch):
    empty_df = pd.DataFrame(columns=["sku", "cost", "currency"])

    def fake_detect(_path):
        return "excel"

    def fake_load(_path):
        return empty_df

    from services.price_importer import io

    monkeypatch.setattr(io, "detect_format", fake_detect, raising=False)
    monkeypatch.setattr(io, "load_file", fake_load, raising=False)

    result = list(io.iter_price_batches(Path("dummy.xlsx"), batch_size=10))
    assert result == []
