import os

import pytest

from services.etl import load_csv as lc

pytestmark = pytest.mark.integration


def _rows(n=3):
    return [{"ASIN": f"A{i:03d}", "qty": i, "price": 9.99 + i} for i in range(n)]


@pytest.mark.parametrize(
    "delimiter,encoding,name",
    [
        (",", "utf-8", "comma.csv"),
        (";", "utf-8", "semicolon.csv"),
        ("\t", "utf-8", "tab.csv"),
        (",", "cp1252", "cp1252.csv"),
    ],
)
def test_csv_delimiters_and_encodings(
    csv_file_factory, ensure_test_generic_table, pg_engine, delimiter, encoding, name
):
    os.environ["TESTING"] = "1"
    p = csv_file_factory(
        headers=["ASIN", "qty", "price"],
        rows=_rows(5),
        delimiter=delimiter,
        encoding=encoding,
        name=name,
    )
    lc.import_file(str(p), dialect="test_generic")
    with pg_engine.connect() as c:
        count = c.execute("SELECT COUNT(*) FROM test_generic_raw").scalar_one()
    assert count == 5


def test_xlsx_happy_path(xlsx_file_factory, ensure_test_generic_table, pg_engine, tmp_path):
    os.environ["TESTING"] = "1"
    p = xlsx_file_factory(headers=["ASIN", "qty", "price"], rows=_rows(4), name="sample.xlsx")
    lc.import_file(str(p), dialect="test_generic")
    with pg_engine.connect() as c:
        count = c.execute("SELECT COUNT(*) FROM test_generic_raw").scalar_one()
    assert count == 4


def test_empty_file_raises_value_error(tmp_path):
    os.environ["TESTING"] = "1"
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(lc.ImportValidationError) as ei:
        lc.import_file(str(empty), dialect="test_generic")
    assert "empty file" in str(ei.value)


def test_missing_required_columns_gives_informative_error(csv_file_factory):
    os.environ["TESTING"] = "1"
    p = csv_file_factory(headers=["ASIN", "qty"], rows=[{"ASIN": "A1", "qty": 1}], name="bad.csv")
    with pytest.raises(lc.ImportValidationError) as ei:
        lc.import_file(str(p), dialect="test_generic")
    assert "missing required columns" in str(ei.value)
