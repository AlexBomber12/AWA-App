from __future__ import annotations

from services.price_importer import reader


def test_load_file_sniffs_delimiter(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "ASIN;Qty;Refund Amount;Currency;Return Date\nA1;1;5.0;EUR;2024-06-01\nA2;2;6.0;EUR;2024-06-02\n"
    )
    df = reader.load_file(csv_path)
    assert df.shape == (2, 5)
