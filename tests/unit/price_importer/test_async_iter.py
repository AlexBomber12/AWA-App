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
    assert batches[0][0].sku == "sku1"
