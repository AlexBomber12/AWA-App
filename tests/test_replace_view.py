from alembic import op

from services.db.utils.views import replace_view


def test_replace_view_executes_drop_and_create(monkeypatch):
    executed: list[str] = []

    def fake_execute(sql: str) -> None:
        executed.append(sql)

    monkeypatch.setattr(op, "execute", fake_execute)

    replace_view("my_view", "SELECT 1")

    assert executed == ["DROP VIEW IF EXISTS my_view CASCADE;", "SELECT 1"]
