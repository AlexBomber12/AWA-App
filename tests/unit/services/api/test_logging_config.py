import logging
from types import SimpleNamespace

import services.api.logging_config as logging_config


def test_request_id_injector_adds_header(monkeypatch):
    event = {}
    result = logging_config._request_id_injector(None, "info", event)
    assert result == {}

    monkeypatch.setattr(logging_config, "correlation_id", SimpleNamespace(get=lambda: "req-99"))
    output = logging_config._request_id_injector(None, "info", {})
    assert output["request_id"] == "req-99"


def test_configure_logging_sets_structlog(monkeypatch):
    captured = {}

    def fake_configure(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(
        logging, "basicConfig", lambda **kwargs: captured.setdefault("basic", kwargs)
    )
    monkeypatch.setattr(logging_config.structlog, "configure", fake_configure)
    logging_config.configure_logging()
    assert "basic" in captured
    assert any(proc for proc in captured["processors"])
