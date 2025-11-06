import json

import awa_common.logging as logging_module
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


def test_bind_user_sub_unbinds_context(capsys) -> None:
    configure_logging(service="api", env="test", version="0.0.0")
    bind_user_sub("u-777")
    bind_user_sub(None)
    bind_request("req-2")
    logger = structlog.get_logger(__name__)
    logger.info("no_user")
    payload = json.loads(capsys.readouterr().out.strip())
    assert "user_sub" not in payload
    clear_context()


def test_bind_request_generates_defaults(capsys) -> None:
    configure_logging(service="api", env="test", version="0.0.0")
    bind_request("", None)
    logger = structlog.get_logger(__name__)
    logger.info("generated")
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["request_id"] == payload["trace_id"]
    assert len(payload["request_id"]) == 36  # uuid4 string length
    clear_context()


def test_extract_trace_id_variants() -> None:
    good = "00-" + "a" * 32 + "-b7-01"
    assert logging_module._extract_trace_id(good) == "a" * 32  # type: ignore[attr-defined]
    assert logging_module._extract_trace_id("invalid") is None  # type: ignore[attr-defined]


def test_bind_celery_task(monkeypatch, capsys) -> None:
    configure_logging(service="worker", env="test", version="1.0.0")

    class DummyRequest:
        id = "task-123"

    class DummyTask:
        request = DummyRequest()

    monkeypatch.setattr(logging_module, "current_task", DummyTask())
    logging_module.bind_celery_task()
    structlog.get_logger(__name__).info("celery_task")
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["task_id"] == "task-123"
    clear_context()
