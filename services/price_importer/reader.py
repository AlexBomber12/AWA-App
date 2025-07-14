from __future__ import annotations

from pathlib import Path
from typing import Any


def detect_format(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    if ext in {".xls", ".xlsx"}:
        return "excel"
    return "csv"


def load_file(path: str | Path) -> Any:
    """Return DataFrame from CSV or Excel file.

    Raises RuntimeError if pandas is unavailable.
    """
    try:
        import pandas as pd
    except ModuleNotFoundError as exc:  # pragma: no cover - env without pandas
        raise RuntimeError("pandas is required to load price files") from exc

    fmt = detect_format(path)
    if fmt == "excel":
        return pd.read_excel(path)
    return pd.read_csv(path)
