from __future__ import annotations

import csv
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

import pandas as pd
import pytest


@pytest.fixture
def csv_file_factory(tmp_path: Path) -> Callable[..., Path]:
    """
    Create a CSV with the provided headers and rows.
    Usage:
      path = csv_file_factory(
          headers=["ASIN","Qty","Price"],
          rows=[{"ASIN":"A1","Qty":1,"Price":9.9}],
          delimiter=",",
          encoding="utf-8",
          name="sample.csv",
      )
    """

    def _make_csv(
        *,
        headers: Sequence[str],
        rows: Iterable[Mapping[str, object]],
        delimiter: str = ",",
        encoding: str = "utf-8",
        name: str = "sample.csv",
    ) -> Path:
        p = tmp_path / name
        with p.open("w", newline="", encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=list(headers), delimiter=delimiter)
            writer.writeheader()
            for r in rows:
                writer.writerow({k: r.get(k, "") for k in headers})
        return p

    return _make_csv


@pytest.fixture
def xlsx_file_factory(tmp_path: Path) -> Callable[..., Path]:
    """
    Create an Excel file with the provided headers and rows.
    """

    def _make_xlsx(
        *,
        headers: Sequence[str],
        rows: Iterable[Mapping[str, object]],
        name: str = "sample.xlsx",
    ) -> Path:
        p = tmp_path / name
        df = pd.DataFrame(list(rows), columns=list(headers))
        df.to_excel(p, index=False)
        return p

    return _make_xlsx


@pytest.fixture
def large_csv_factory(csv_file_factory) -> Callable[..., Path]:
    """
    Quickly generate a large CSV for performance/dedup tests.
    Fields: ASIN, qty, price
    """

    def _make_large_csv(
        n: int,
        *,
        name: str = "large.csv",
        delimiter: str = ",",
        encoding: str = "utf-8",
    ) -> Path:
        headers = ["ASIN", "qty", "price"]
        rows = ({"ASIN": f"A{i:05d}", "qty": i % 5, "price": float(i % 100)} for i in range(n))
        return csv_file_factory(
            headers=headers,
            rows=rows,
            delimiter=delimiter,
            encoding=encoding,
            name=name,
        )

    return _make_large_csv
