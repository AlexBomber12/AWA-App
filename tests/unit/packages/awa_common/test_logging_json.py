import json

import structlog
from awa_common.logging import bind_request, bind_user_sub, clear_context, configure_logging


def test_configure_logging_emits_json_with_context(capsys) -> None:
    configure_logging(service="api", env="test", version="0.0.0")
    bind_user_sub("u-123")
    bind_request("req-1", "trace-xyz")

    logger = structlog.get_logger(__name__)
    logger.info("sample_event", status="ok")

    captured = capsys.readouterr().out.strip()
    assert captured

    payload = json.loads(captured)
    assert payload["event"] == "sample_event"
    assert payload["service"] == "api"
    assert payload["env"] == "test"
    assert payload["version"] == "0.0.0"
    assert payload["request_id"] == "req-1"
    assert payload["trace_id"] == "trace-xyz"
    assert payload["user_sub"] == "u-123"
    assert payload["status"] == "ok"
    assert payload["level"] == "info"
    assert "timestamp" in payload
    clear_context()
