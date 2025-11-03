import datetime

from services.api.routes import stats as stats_module


class DummyMappings:
    def __init__(self, rows):
        self.rows = rows

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return self.rows


class DummyDB:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def execute(self, stmt):
        key = str(stmt)
        self.calls.append(key)
        return DummyResult(self.results.get(key, []))


class DummyResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return DummyMappings(self._rows)


def test_kpi_sql_branch(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats_module, "_roi_view_name", lambda: "v_roi_full")
    rows = [{"roi_avg": 1.5, "products": 2, "vendors": 1}]
    db = DummyDB({"SELECT AVG": rows})

    def fake_execute(stmt):
        return DummyResult(rows)

    db.execute = fake_execute
    result = stats_module.kpi(db=db)
    assert result["kpi"]["roi_avg"] == 1.5


def test_roi_by_vendor_returns_items(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats_module, "_roi_view_name", lambda: "v_roi_full")
    rows = [
        {"vendor": "A", "roi_avg": 2.5, "items": 3},
        {"vendor": "B", "roi_avg": None, "items": None},
    ]

    class DummyDB2:
        def execute(self, stmt):
            return DummyResult(rows)

    resp = stats_module.roi_by_vendor(db=DummyDB2())
    assert resp["total_vendors"] == 2
    assert resp["items"][0]["vendor"] == "A"


def test_roi_trend_handles_multiple_columns(monkeypatch):
    monkeypatch.setenv("STATS_USE_SQL", "1")
    monkeypatch.setattr(stats_module, "_roi_view_name", lambda: "v_roi_full")
    calls = {"dt": RuntimeError("no column"), "date": RuntimeError("nope")}

    class DummyDB3:
        def execute(self, stmt):
            text = str(stmt)
            if "snapshot_date" in text:
                rows = [{"month": datetime.date(2024, 1, 1), "roi_avg": 1.2, "items": 5}]
                return DummyResult(rows)
            for key, exc in calls.items():
                if key in text:
                    raise exc
            return DummyResult([])

    resp = stats_module.roi_trend(db=DummyDB3())
    assert resp["points"][0]["month"] == "2024-01-01"
