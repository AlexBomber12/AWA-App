from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import pandas as pd

from etl import load_csv
from services.etl import healthcheck


class _StubCursor:
    def __init__(self, connection: _StubConnection):
        self._connection = connection

    def __enter__(self) -> _StubCursor:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, sql: str, params=None) -> None:
        self._connection.statements.append((sql, params))

    def fetchone(self):
        if self._connection.fetch_plan:
            return self._connection.fetch_plan.popleft()
        return None


class _StubConnection:
    def __init__(self, fetch_plan: list | None = None) -> None:
        self.fetch_plan: deque = deque(fetch_plan or [])
        self.statements: list[tuple[str, object]] = []
        self.autocommit = False
        self.committed = False
        self.closed = False

    def cursor(self) -> _StubCursor:
        return _StubCursor(self)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


@dataclass
class _StubEngine:
    connection: _StubConnection
    disposed: bool = False

    def raw_connection(self) -> _StubConnection:
        return self.connection

    def dispose(self) -> None:
        self.disposed = True


def _fake_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "asin": ["A1"],
            "qty": [1],
            "refund_amount": [2.5],
            "return_reason": ["damaged"],
            "return_date": ["2024-01-01"],
            "currency": ["EUR"],
        }
    )


def test_import_file_skips_when_already_logged(monkeypatch, tmp_path) -> None:
    file_path = tmp_path / "returns.csv"
    file_path.write_text("asin,qty,refund_amount\nA1,1,2.5\n")

    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("INGEST_IDEMPOTENT", "true")
    monkeypatch.setenv("ANALYZE_MIN_ROWS", "9999")
    monkeypatch.setattr(load_csv, "USE_COPY", True)
    monkeypatch.setattr(load_csv, "_read_csv_flex", lambda path: _fake_df())
    monkeypatch.setattr(load_csv.amazon_returns, "normalise", lambda df: df)
    monkeypatch.setattr(load_csv.schemas, "validate", lambda df, dialect: df)
    monkeypatch.setattr(load_csv, "build_dsn", lambda sync=True: "postgresql://test")

    copy_calls: list[tuple] = []
    monkeypatch.setattr(
        load_csv,
        "copy_df_via_temp",
        lambda *args, **kwargs: copy_calls.append((args, kwargs)),
    )

    conn = _StubConnection(fetch_plan=[(1,)])

    def _create_engine(*args, **kwargs):
        return _StubEngine(conn)

    monkeypatch.setattr(load_csv, "create_engine", _create_engine)

    result = load_csv.import_file(str(file_path), report_type="returns_report")
    assert result["status"] == "skipped"
    assert result["rows"] == 0
    assert conn.committed is True
    assert copy_calls == []


def test_import_file_success_then_skip(monkeypatch, tmp_path) -> None:
    file_path = tmp_path / "returns.csv"
    file_path.write_text("asin,qty,refund_amount\nA1,1,2.5\n")

    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("INGEST_IDEMPOTENT", "true")
    monkeypatch.setenv("ANALYZE_MIN_ROWS", "9999")
    monkeypatch.setattr(load_csv, "USE_COPY", True)
    monkeypatch.setattr(load_csv, "_read_csv_flex", lambda path: _fake_df())
    monkeypatch.setattr(load_csv.amazon_returns, "normalise", lambda df: df)
    monkeypatch.setattr(load_csv.schemas, "validate", lambda df, dialect: df)
    monkeypatch.setattr(load_csv, "build_dsn", lambda sync=True: "postgresql://test")

    copy_calls: list[tuple] = []

    def _copy_hook(*args, **kwargs):
        copy_calls.append((args, kwargs))
        return None

    monkeypatch.setattr(load_csv, "copy_df_via_temp", _copy_hook)

    first_conn = _StubConnection()
    second_conn = _StubConnection(fetch_plan=[(1,)])
    engines = deque([_StubEngine(first_conn), _StubEngine(second_conn)])

    def _create_engine(*args, **kwargs):
        engine = engines.popleft()
        return engine

    monkeypatch.setattr(load_csv, "create_engine", _create_engine)

    first = load_csv.import_file(str(file_path), report_type="returns_report")
    assert first["status"] == "success"
    assert copy_calls
    assert first_conn.committed is True
    assert first_conn.closed is True

    second = load_csv.import_file(str(file_path), report_type="returns_report")
    assert second["status"] == "skipped"
    assert len(copy_calls) == 1  # no additional copy
    assert second_conn.committed is True
    assert second_conn.closed is True


def test_sha256_file_changes_with_content(tmp_path) -> None:
    file_path = tmp_path / "sample.csv"
    file_path.write_text("asin,qty\nA1,1\n")
    first = load_csv._sha256_file(file_path)
    file_path.write_text("asin,qty\nA1,2\n")
    second = load_csv._sha256_file(file_path)
    assert first != second
    file_path.write_text("asin,qty\nA1,2\n")
    assert load_csv._sha256_file(file_path) == second


def test_retry_eventually_succeeds(monkeypatch) -> None:
    attempt = {"count": 0}
    sleeps: list[float] = []

    def _flaky():
        attempt["count"] += 1
        if attempt["count"] < 2:
            raise RuntimeError("boom")

    monkeypatch.setattr(healthcheck.time, "sleep", lambda delay: sleeps.append(delay))
    assert healthcheck._retry(_flaky, attempts=3, delay=0.1, name="flaky")
    assert attempt["count"] == 2
    assert sleeps  # one backoff recorded


def test_retry_failure(monkeypatch) -> None:
    monkeypatch.setattr(healthcheck.time, "sleep", lambda delay: None)

    def _always_fail():
        raise RuntimeError("nope")

    assert healthcheck._retry(_always_fail, attempts=2, delay=0.01, name="fail") is False


def test_import_file_force_bypasses_idempotent_skip(monkeypatch, tmp_path) -> None:
    file_path = tmp_path / "returns.csv"
    file_path.write_text("asin,qty,refund_amount\nA1,1,2.5\n")

    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("INGEST_IDEMPOTENT", "true")
    monkeypatch.setattr(load_csv, "USE_COPY", True)
    monkeypatch.setattr(load_csv, "_read_csv_flex", lambda path: _fake_df())
    monkeypatch.setattr(load_csv.amazon_returns, "normalise", lambda df: df)
    monkeypatch.setattr(load_csv.schemas, "validate", lambda df, dialect: df)
    monkeypatch.setattr(load_csv, "build_dsn", lambda sync=True: "postgresql://test")

    copy_calls: list[tuple] = []

    def _copy_hook(*args, **kwargs):
        copy_calls.append((args, kwargs))
        return None

    monkeypatch.setattr(load_csv, "copy_df_via_temp", _copy_hook)

    conn = _StubConnection(fetch_plan=[(1,)])

    def _create_engine(*args, **kwargs):
        return _StubEngine(conn)

    monkeypatch.setattr(load_csv, "create_engine", _create_engine)

    result = load_csv.import_file(str(file_path), report_type="returns_report", force=True)
    assert result["status"] == "success"
    assert copy_calls, "copy should execute when force=True"
