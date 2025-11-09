from __future__ import annotations

from services.api import db as db_module


def test_async_session_uses_session_factory(monkeypatch):
    class DummySession: ...

    monkeypatch.setattr(db_module, "get_sessionmaker", lambda: (lambda: DummySession()))
    session = db_module.async_session()
    assert isinstance(session, DummySession)
