from pathlib import Path
import pandas as pd


def detect_format(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    if ext in {".xls", ".xlsx"}:
        return "excel"
    return "csv"


def load_file(path: str | Path) -> pd.DataFrame:
    fmt = detect_format(path)
    if fmt == "excel":
        return pd.read_excel(path)
    return pd.read_csv(path)
