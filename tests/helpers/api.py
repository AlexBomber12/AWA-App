from __future__ import annotations

from services.api import main


async def async_noop(*_args, **_kwargs):
    return None


async def async_true(*_args, **_kwargs):
    return True


def prepare_api_for_tests(monkeypatch) -> None:
    """Patch expensive startup/shutdown hooks so TestClient can run without Redis/DB."""
    monkeypatch.setattr(main.settings, "STATS_ENABLE_CACHE", False, raising=False)
    monkeypatch.setattr(main, "_wait_for_db", async_noop)
    monkeypatch.setattr(main, "_wait_for_redis", async_noop)
    monkeypatch.setattr(main, "_check_llm", async_noop)
    monkeypatch.setattr(main, "configure_cache_backend", async_noop)
    monkeypatch.setattr(main, "close_cache", async_noop)
    monkeypatch.setattr(main, "ping_cache", async_true)
