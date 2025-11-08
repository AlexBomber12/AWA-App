import json

import structlog

from awa_common import logging as logging_module


def test_configure_logging_sets_context(monkeypatch, capsys):
    monkeypatch.setattr(logging_module.settings, "ENV", "test")
    monkeypatch.setattr(logging_module.settings, "APP_VERSION", "9.9.9")
    logging_module.configure_logging(service="worker", level="INFO")
    logging_module.set_request_context("req-123", "trace-456")

    logger = structlog.get_logger("observability")
    logger.info("hello_world", component="unit_test")

    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["service"] == "worker"
    assert payload["env"] == "test"
    assert payload["version"] == "9.9.9"
    assert payload["request_id"] == "req-123"
    assert payload["trace_id"] == "trace-456"
    assert payload["msg"] == "hello_world"
    assert payload["component"] == "unit_test"
    assert "ts" in payload
    logging_module.clear_request_context()
