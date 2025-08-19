import pandas as pd

NAME = "test_generic"
TABLE = "test_generic_raw"
REQUIRED_COLUMNS = ["ASIN", "qty", "price"]
UNIQUE_KEY = ["ASIN"]


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    # Keep exactly required columns, coerce dtypes
    df = df.rename(columns={c: c for c in df.columns})  # no-op, explicit
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {','.join(missing)}")
    out = df[REQUIRED_COLUMNS].copy()
    out["ASIN"] = out["ASIN"].astype(str)
    out["qty"] = pd.to_numeric(out["qty"], errors="coerce").fillna(0).astype(int)
    out["price"] = pd.to_numeric(out["price"], errors="coerce")
    return out
