import pandas as pd
from services.price_importer.normaliser import guess_columns, normalise


def test_guess_columns():
    df = pd.DataFrame(columns=["ASIN", "Unit Cost", "MOQ"])
    cols = guess_columns(df)
    assert cols["sku"] == "ASIN"
    assert cols["cost"] == "Unit Cost"


def test_normalise():
    df = pd.DataFrame({"ASIN": ["A1"], "Unit Cost": [1.0], "MOQ": [1]})
    out = normalise(df)
    assert list(out.columns) == ["sku", "cost", "moq"]
