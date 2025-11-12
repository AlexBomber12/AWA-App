from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace

import pytest


def _load_module(monkeypatch: pytest.MonkeyPatch):
    fake_sync = SimpleNamespace(async_to_sync=lambda fn: fn)
    monkeypatch.setitem(sys.modules, "asgiref", SimpleNamespace(sync=fake_sync))
    monkeypatch.setitem(sys.modules, "asgiref.sync", fake_sync)
    from services.alert_bot import alert_bot as module

    return importlib.reload(module)


def test_alert_bot_main(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module(monkeypatch)

    called = {"evaluated": False}

    def fake_eval():
        called["evaluated"] = True
        return {"status": "ok"}

    monkeypatch.setattr(module, "_evaluate_sync", fake_eval)

    assert module.main() == 0
    assert called == {"evaluated": True}
