from __future__ import annotations

from pathlib import Path
from typing import Any


def detect_format(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    if ext in {".xls", ".xlsx"}:
        return "excel"
    return "csv"


def _read_csv_flex(path: str | Path) -> Any:
    import pandas as pd

    for enc in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            return pd.read_csv(path, sep=None, engine="python", encoding=enc)
        except UnicodeDecodeError:
            continue
        except Exception:
            pass
    for sep in (",", ";", "\t", "|"):
        try:
            return pd.read_csv(path, sep=sep)
        except Exception:
            continue
    raise RuntimeError(f"Failed to read CSV: {path}")


def load_file(path: str | Path) -> Any:
    try:
        import pandas as pd
    except ModuleNotFoundError as exc:  # pragma: no cover - env without pandas
        raise RuntimeError("pandas is required to load price files") from exc
    fmt = detect_format(path)
    if fmt == "excel":
        return pd.read_excel(path)
    return _read_csv_flex(path)
