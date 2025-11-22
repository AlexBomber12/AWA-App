from __future__ import annotations

import gzip
from collections import deque
from typing import Any

import pytest

from etl import load_csv


class _StubCursor:
    def __init__(self, connection: _StubConnection):
        self._connection = connection

    def __enter__(self) -> _StubCursor:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - helper
        return None

    def execute(self, sql: str, params=None) -> None:
        self._connection.statements.append((sql, params))

    def fetchone(self):
        if self._connection.fetch_plan:
            return self._connection.fetch_plan.popleft()
        return None


class _StubConnection:
    def __init__(self, fetch_plan: list[Any] | None = None):
        self.fetch_plan: deque[Any] = deque(fetch_plan or [])
        self.statements: list[tuple[str, Any]] = []
        self.autocommit = False
        self.closed = False
        self.committed = False

    def cursor(self) -> _StubCursor:
        return _StubCursor(self)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


class _StubEngine:
    def __init__(self, connection: _StubConnection):
        self._connection = connection
        self.disposed = False

    def raw_connection(self) -> _StubConnection:
        return self._connection

    def dispose(self) -> None:
        self.disposed = True


def _flatten(batches: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    combined: list[dict[str, Any]] = []
    for batch in batches:
        combined.extend(batch)
    return combined


def test_load_large_csv_streams_chunks(tmp_path) -> None:
    csv_path = tmp_path / "returns.csv"
    header = "asin,qty,refund_amount,return_reason,return_date,currency"
    rows = [
        header,
        *(f"ASIN{i:03d},1,2.5,damaged,2024-01-01,USD" for i in range(105)),
    ]
    csv_path.write_text("\n".join(rows), encoding="utf-8")

    chunks = list(load_csv.load_large_csv(csv_path, chunk_size=20))
    assert len(chunks) >= 5  # multiple chunks expected
    assert sum(len(chunk) for chunk in chunks) == 105


def test_load_large_csv_streams_gz_chunks(tmp_path) -> None:
    csv_path = tmp_path / "returns.csv.gz"
    header = "asin,qty,refund_amount,return_reason,return_date,currency"
    rows = [
        header,
        *(f"ASIN{i:03d},1,2.5,damaged,2024-01-01,USD" for i in range(40)),
    ]
    with gzip.open(csv_path, "wb") as handle:
        handle.write("\n".join(rows).encode("utf-8"))

    chunks = list(load_csv.load_large_csv(csv_path, chunk_size=10))
    assert len(chunks) >= 4
    assert sum(len(chunk) for chunk in chunks) == 40


@pytest.mark.parametrize("extension", ["csv", "csv.gz", "xlsx"])
def test_import_file_streaming_matches_full_load(monkeypatch, tmp_path, extension, xlsx_file_factory) -> None:
    columns = ["asin", "qty", "refund_amount", "return_reason", "return_date", "currency"]
    records = [
        {
            "asin": f"ASIN{i:03d}",
            "qty": i % 3 + 1,
            "refund_amount": 2.5,
            "return_reason": "damaged",
            "return_date": f"2024-01-{(i % 28) + 1:02d}",
            "currency": "USD",
        }
        for i in range(60)
    ]

    if extension == "xlsx":
        csv_path = xlsx_file_factory(headers=columns, rows=records, name="returns.xlsx")
    else:
        lines = [",".join(columns)]
        for rec in records:
            lines.append(
                f"{rec['asin']},{rec['qty']},{rec['refund_amount']},{rec['return_reason']},{rec['return_date']},{rec['currency']}"
            )
        csv_path = tmp_path / f"returns.{extension}"
        content = "\n".join(lines).encode("utf-8")
        if extension.endswith(".gz"):
            with gzip.open(csv_path, "wb") as handle:
                handle.write(content)
        else:
            csv_path.write_bytes(content)

    monkeypatch.setenv("INGEST_IDEMPOTENT", "false")
    monkeypatch.setenv("ANALYZE_MIN_ROWS", "999999")
    monkeypatch.setattr(load_csv, "USE_COPY", True)
    monkeypatch.setattr(load_csv, "build_dsn", lambda sync=True: "postgresql://test")
    monkeypatch.setattr(load_csv.schemas, "validate", lambda df, dialect: df)

    def run(streaming: bool) -> tuple[dict[str, Any], list[list[dict[str, Any]]]]:
        batches: list[list[dict[str, Any]]] = []

        def fake_copy(engine, df, **kwargs):
            batches.append(df.to_dict(orient="records"))
            return len(df)

        monkeypatch.setattr(load_csv, "copy_df_via_temp", fake_copy)
        conn = _StubConnection()
        engine = _StubEngine(conn)
        monkeypatch.setattr(load_csv, "create_engine", lambda *args, **kwargs: engine)
        result = load_csv.import_file(str(csv_path), report_type="returns_report", streaming=streaming)
        return result, batches

    eager_result, eager_batches = run(streaming=False)
    streaming_result, streaming_batches = run(streaming=True)

    assert eager_result["rows"] == streaming_result["rows"] == 60
    assert eager_result["status"] == streaming_result["status"] == "success"
    assert eager_result["dialect"] == streaming_result["dialect"] == "returns_report"
    assert eager_result["streaming"] is False
    assert streaming_result["streaming"] is True
    assert _flatten(eager_batches) == _flatten(streaming_batches)
