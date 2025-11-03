import os
from pathlib import Path

import psycopg2
import pytest

from etl.load_csv import import_file

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL not set"),
]


def _run(monkeypatch, threshold: int) -> list[str]:
    monkeypatch.setenv("ANALYZE_MIN_ROWS", str(threshold))
    calls: list[str] = []
    orig = psycopg2.extensions.cursor.execute

    def spy(self, query, vars=None):  # type: ignore[override]
        if isinstance(query, str) and query.lower().startswith("analyze"):
            calls.append(query)
        return orig(self, query, vars)

    monkeypatch.setattr(psycopg2.extensions.cursor, "execute", spy)
    csv = Path("tests/fixtures/sample_returns.csv")
    import_file(str(csv), force=True)
    return calls


def test_analyze_triggered(monkeypatch):
    calls = _run(monkeypatch, 1)
    assert any("analyze" in c.lower() for c in calls)


def test_analyze_not_triggered(monkeypatch):
    calls = _run(monkeypatch, 1000)
    assert not any("analyze" in c.lower() for c in calls)
