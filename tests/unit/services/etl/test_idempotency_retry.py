from __future__ import annotations

import pandas as pd
import pytest

from etl import load_csv
from services.etl import healthcheck


class _StubSession:
    def __init__(self) -> None:
        self.closed = False

    def commit(self) -> None:  # pragma: no cover - no-op
        return None

    def rollback(self) -> None:  # pragma: no cover - no-op
        return None

    def close(self) -> None:
        self.closed = True

    def execute(self, *_args, **_kwargs):  # pragma: no cover - updated via stub_load_log
        return None


class _StubCursor:
    def __init__(self, connection: _StubConnection):
        self.connection = connection
        self.statements: list[tuple[str, object | None]] = []

    def __enter__(self) -> _StubCursor:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, sql: str, params=None) -> None:
        self.statements.append((sql, params))
        self.connection.statements.append((sql, params))


class _StubConnection:
    def __init__(self) -> None:
        self.autocommit = False
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.statements: list[tuple[str, object | None]] = []

    def cursor(self) -> _StubCursor:
        return _StubCursor(self)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


class _StubEngine:
    def __init__(self, conn: _StubConnection):
        self.connection = conn
        self.disposed = False

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


def _install_stubs(
    monkeypatch: pytest.MonkeyPatch,
    stub_load_log,
    conn: _StubConnection,
    *,
    validation_error: bool = False,
):
    copy_calls: list[tuple] = []
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("INGEST_IDEMPOTENT", "true")
    monkeypatch.setattr(load_csv, "USE_COPY", True)
    monkeypatch.setattr(load_csv, "_read_csv_flex", lambda path: _fake_df())
    monkeypatch.setattr(load_csv, "_resolve_dialect", lambda df, explicit: ("returns_report", df))
    monkeypatch.setattr(load_csv, "build_dsn", lambda sync=True: "postgresql://test")
    monkeypatch.setattr(load_csv, "copy_df_via_temp", lambda *a, **k: copy_calls.append((a, k)))
    monkeypatch.setattr(load_csv, "create_engine", lambda *a, **k: _StubEngine(conn))
    monkeypatch.setattr(load_csv, "sessionmaker", lambda *a, **k: (lambda: _StubSession()))
    if validation_error:
        monkeypatch.setattr(load_csv.schemas, "validate", lambda df, dialect: (_ for _ in ()).throw(ValueError("bad")))
    else:
        monkeypatch.setattr(load_csv.schemas, "validate", lambda df, dialect: df)
    return copy_calls


def test_import_file_skips_when_already_logged(monkeypatch, tmp_path, stub_load_log) -> None:
    file_path = tmp_path / "returns.csv"
    file_path.write_text("asin,qty,refund_amount\nA1,1,2.5\n")
    conn = _StubConnection()
    copy_calls = _install_stubs(monkeypatch, stub_load_log, conn)

    first = load_csv.import_file(str(file_path), report_type="returns_report")
    second = load_csv.import_file(str(file_path), report_type="returns_report")

    assert first["status"] == "success"
    assert second["status"] == "skipped"
    assert len(copy_calls) == 1
    statuses = {record["status"] for record in stub_load_log.values()}
    assert "skipped" in statuses


def test_import_file_force_bypasses_idempotent_skip(monkeypatch, tmp_path, stub_load_log) -> None:
    file_path = tmp_path / "returns.csv"
    file_path.write_text("asin,qty,refund_amount\nA1,1,2.5\n")
    conn = _StubConnection()
    copy_calls = _install_stubs(monkeypatch, stub_load_log, conn)

    first = load_csv.import_file(str(file_path), report_type="returns_report")
    assert first["status"] == "success"
    second = load_csv.import_file(str(file_path), report_type="returns_report", force=True)
    assert second["status"] == "success"
    assert len(copy_calls) == 2
    assert len(stub_load_log) == 2


def test_import_file_validation_failure(monkeypatch, tmp_path, stub_load_log) -> None:
    file_path = tmp_path / "returns.csv"
    file_path.write_text("asin,qty,refund_amount\nA1,1,2.5\n")
    conn = _StubConnection()
    _install_stubs(monkeypatch, stub_load_log, conn, validation_error=True)

    with pytest.raises(load_csv.ImportValidationError):
        load_csv.import_file(str(file_path), report_type="returns_report")
    statuses = {record["status"] for record in stub_load_log.values()}
    assert "failed" in statuses
    assert conn.rolled_back is True


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
