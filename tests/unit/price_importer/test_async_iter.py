from __future__ import annotations

import pytest

from services.price_importer import io as importer_io


@pytest.mark.asyncio
async def test_iter_price_batches_async(tmp_path):
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text("sku,cost,currency\nsku1,1,eur\n", encoding="utf-8")
    batches = []
    async for batch in importer_io.iter_price_batches(csv_path, batch_size=1, max_workers=1):
        batches.append(batch)
    assert len(batches) == 1
    assert batches[0][0]["sku"] == "sku1"


def test_frame_iterator_csv(tmp_path):
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text("sku,cost,currency\nsku1,1,eur\n", encoding="utf-8")
    iterator = importer_io._frame_iterator(csv_path, 1)
    frame = next(iterator)
    assert not frame.empty


def test_frame_iterator_rejects_format(monkeypatch, tmp_path):
    other = tmp_path / "prices.txt"
    other.write_text("sku,cost\n", encoding="utf-8")

    monkeypatch.setattr(importer_io, "detect_format", lambda _p: "binary")
    with pytest.raises(RuntimeError):
        importer_io._frame_iterator(other, 1)
