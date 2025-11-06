import builtins
import importlib
import sys
from types import SimpleNamespace

import pytest
from awa_common import metrics
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from starlette.requests import Request


@pytest.fixture(autouse=True)
def _reset_metrics_globals():
    metrics.init(service="api", env="test", version="1.0.0")
    metrics.HTTP_REQUESTS_TOTAL.clear()
    metrics.HTTP_REQUEST_DURATION_SECONDS.clear()
    metrics.TASK_RUNS_TOTAL.clear()
    metrics.TASK_DURATION_SECONDS.clear()
    metrics.TASK_FAILURES_TOTAL.clear()
    metrics.ETL_RUNS_TOTAL.clear()
    metrics.ETL_FAILURES_TOTAL.clear()
    metrics.ETL_RETRY_TOTAL.clear()
    metrics.ETL_DURATION_SECONDS.clear()
    metrics.QUEUE_BACKLOG.clear()
    metrics._TASK_START.clear()
    metrics._BACKLOG_THREAD = None
    metrics._CELERY_METRICS_ENABLED = False
    yield
    metrics._BACKLOG_THREAD = None


def test_create_registry_uses_multiprocess(monkeypatch):
    calls = []

    class FakeCollector:
        def __init__(self, registry):
            calls.append(registry)

    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", "/tmp/prom")
    monkeypatch.setattr(metrics, "MultiProcessCollector", FakeCollector)
    registry = metrics._create_registry()
    assert calls == [registry]


def test_metrics_middleware_records_non_200(monkeypatch):
    app = FastAPI()
    app.add_middleware(metrics.MetricsMiddleware)

    @app.get("/teapot")
    async def teapot():
        raise HTTPException(status_code=418)

    @app.get("/explode")
    async def explode():
        raise RuntimeError("boom")

    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/teapot").status_code == 418
    assert client.get("/explode").status_code == 500

    samples = metrics.HTTP_REQUESTS_TOTAL.collect()[0].samples
    statuses = {(sample.labels["path_template"], sample.labels["status"]) for sample in samples}
    assert ("/teapot", "418") in statuses
    assert ("/explode", "500") in statuses


@pytest.mark.asyncio
async def test_metrics_middleware_handles_http_exception():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/async-http",
        "headers": [],
        "app": SimpleNamespace(),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    request = Request(scope, receive)

    middleware = metrics.MetricsMiddleware(lambda scope: None)

    async def failing_next(_request):
        raise HTTPException(status_code=429)

    with pytest.raises(HTTPException):
        await middleware.dispatch(request, failing_next)

    samples = metrics.HTTP_REQUESTS_TOTAL.collect()[0].samples
    status_codes = {sample.labels["status"] for sample in samples}
    assert "429" in status_codes


@pytest.mark.asyncio
async def test_metrics_middleware_handles_unexpected_exception():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/async-error",
        "headers": [],
        "app": SimpleNamespace(),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    request = Request(scope, receive)
    middleware = metrics.MetricsMiddleware(lambda scope: None)

    async def bomb(_request):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await middleware.dispatch(request, bomb)

    samples = metrics.HTTP_REQUESTS_TOTAL.collect()[0].samples
    status_codes = {sample.labels["status"] for sample in samples}
    assert "500" in status_codes


def test_path_template_variants():
    def make_request(route_obj, path="/alpha/123"):
        return SimpleNamespace(scope={"route": route_obj}, url=SimpleNamespace(path=path))

    request = make_request(SimpleNamespace(path="/alpha/{id}"))
    assert metrics._path_template(request) == "/alpha/{id}"

    request = make_request(SimpleNamespace(path=None, path_format="/beta/{name}"))
    assert metrics._path_template(request) == "/beta/{name}"

    class Formatter:
        def __str__(self) -> str:
            return "/gamma/{slug}"

    request = make_request(SimpleNamespace(path=None, path_format=Formatter()))
    assert metrics._path_template(request) == "/gamma/{slug}"

    request = make_request(None, path="/omega/42")
    assert metrics._path_template(request) == "/omega/42"

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/sigma/7",
        "headers": [],
        "app": SimpleNamespace(),
        "route": None,
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    starlette_request = Request(scope, receive)
    assert metrics._path_template(starlette_request) == "/sigma/7"

    plain_request = SimpleNamespace(scope={}, url=SimpleNamespace(path="/zeta"))
    assert metrics._path_template(plain_request) == "/zeta"


def test_register_metrics_endpoint_returns_payload():
    app = FastAPI()
    metrics.register_metrics_endpoint(app)
    with TestClient(app) as client:
        response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == metrics.CONTENT_TYPE_LATEST


def test_task_label_fallbacks():
    class WithName:
        name = "demo.task"

    class NoName:
        pass

    assert metrics._task_label(WithName()) == "demo.task"
    assert metrics._task_label("simple") == "simple"
    assert metrics._task_label(NoName()) == "NoName"

    class ReallyWeird:
        def __getattribute__(self, item):
            if item == "name":
                raise AttributeError
            if item == "__class__":
                return SimpleNamespace(__name__=None)
            return super().__getattribute__(item)

    assert metrics._task_label(ReallyWeird()) == "unknown"


def test_on_task_prerun_without_id():
    metrics.on_task_prerun(sender=SimpleNamespace(name="demo"), task_id="")
    assert metrics._TASK_START == {}


def test_task_signal_flow(monkeypatch):
    times = iter([1.0, 2.5, 3.5])
    monkeypatch.setattr(metrics.time, "perf_counter", lambda: next(times))

    class Sender:
        name = "pipeline.task"

    metrics.on_task_prerun(sender=Sender(), task_id="task-1")
    metrics.on_task_postrun(sender=Sender(), task_id="task-1", state="SUCCESS")
    metrics.on_task_failure(sender=Sender(), task_id="task-1", exception=RuntimeError("oops"))

    runs = metrics.TASK_RUNS_TOTAL.collect()[0].samples
    labels = {(sample.labels["task_name"], sample.labels["outcome"]) for sample in runs}
    assert ("pipeline.task", "success") in labels
    failures = metrics.TASK_FAILURES_TOTAL.collect()[0].samples
    assert any(sample.labels["exc_type"] == "RuntimeError" for sample in failures)
    durations = metrics.TASK_DURATION_SECONDS.collect()[0].samples
    assert any(sample.name.endswith("_sum") for sample in durations)


def test_backlog_probe_import_failure(monkeypatch):
    metrics._maybe_start_backlog_probe(
        broker_url="sqs://queue", queue_names=["primary"], interval=5
    )

    def fake_import(name, *args, **kwargs):
        if name == "redis":
            raise ImportError("redis missing")
        return builtins.__import__(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    metrics._maybe_start_backlog_probe(
        broker_url="redis://localhost/0", queue_names=["primary"], interval=5
    )
    assert metrics._BACKLOG_THREAD is None


def test_backlog_probe_start_to_finish(monkeypatch):
    class FakeRedisClient:
        def __init__(self):
            self.queues: list[str] = []

        def llen(self, queue: str) -> int:
            self.queues.append(queue)
            if queue == "skip":
                raise RuntimeError("temporary failure")
            return 7

    clients: list[FakeRedisClient] = []

    class FakeRedisModule:
        class Redis:
            @staticmethod
            def from_url(_url, decode_responses=False):
                _ = decode_responses
                client = FakeRedisClient()
                clients.append(client)
                return client

    monkeypatch.setitem(sys.modules, "redis", FakeRedisModule)

    def fake_sleep(_):
        raise StopIteration

    monkeypatch.setattr(metrics.time, "sleep", fake_sleep)

    class FakeThread:
        def __init__(self, target, name, daemon):
            self._target = target
            self.started = False

        def start(self):
            self.started = True
            try:
                self._target()
            except StopIteration:
                pass

    monkeypatch.setattr(metrics.threading, "Thread", FakeThread)

    metrics._maybe_start_backlog_probe(
        broker_url="redis://localhost/0", queue_names=["skip", "main"], interval=1
    )

    assert isinstance(metrics._BACKLOG_THREAD, FakeThread)
    samples = metrics.QUEUE_BACKLOG.collect()[0].samples
    assert any(sample.labels.get("queue") == "main" for sample in samples)
    metrics._BACKLOG_THREAD = None
    sys.modules.pop("redis", None)


def test_backlog_probe_when_thread_exists():
    sentinel = object()
    metrics._BACKLOG_THREAD = sentinel
    metrics._maybe_start_backlog_probe(
        broker_url="redis://localhost/0", queue_names=["main"], interval=5
    )
    assert metrics._BACKLOG_THREAD is sentinel
    metrics._BACKLOG_THREAD = None


def test_backlog_probe_empty_queue_list():
    metrics._maybe_start_backlog_probe(
        broker_url="redis://localhost/0", queue_names=["", None], interval=5
    )
    assert metrics._BACKLOG_THREAD is None


def test_backlog_probe_handles_connection_error(monkeypatch):
    class FailingRedisModule:
        class Redis:
            @staticmethod
            def from_url(_url, decode_responses=False):
                _ = decode_responses
                raise RuntimeError("connection failed")

    monkeypatch.setitem(sys.modules, "redis", FailingRedisModule)
    metrics._maybe_start_backlog_probe(
        broker_url="redis://localhost/0", queue_names=["primary"], interval=5
    )
    assert metrics._BACKLOG_THREAD is not None
    sys.modules.pop("redis", None)
    metrics._BACKLOG_THREAD = None


def test_start_worker_metrics_http_variants(monkeypatch):
    monkeypatch.delenv("WORKER_METRICS_HTTP", raising=False)
    metrics.start_worker_metrics_http_if_enabled()

    called: dict[str, int] = {}

    def fake_start_http_server(port, registry):
        called["port"] = port
        called["registry"] = registry

    monkeypatch.setattr(metrics, "start_http_server", fake_start_http_server)
    monkeypatch.setenv("WORKER_METRICS_HTTP", "1")
    monkeypatch.setenv("WORKER_METRICS_PORT", "not-a-number")
    metrics.start_worker_metrics_http_if_enabled()
    assert called["port"] == 9108
    assert called["registry"] is metrics.REGISTRY


def test_enable_celery_metrics_idempotent(monkeypatch):
    class _Connector:
        def __init__(self):
            self.calls = 0

        def connect(self, handler, weak=False):
            self.calls += 1

    fake_signals = SimpleNamespace(
        task_prerun=_Connector(),
        task_postrun=_Connector(),
        task_failure=_Connector(),
    )
    fake_celery = SimpleNamespace(signals=fake_signals)
    monkeypatch.setitem(sys.modules, "celery", fake_celery)

    metrics.enable_celery_metrics(object(), broker_url=None, queue_names=None)
    first_calls = fake_signals.task_prerun.calls
    metrics.enable_celery_metrics(object(), broker_url=None, queue_names=None)
    assert fake_signals.task_prerun.calls == first_calls
    sys.modules.pop("celery", None)


def test_celery_queue_names_split(monkeypatch):
    monkeypatch.setenv("ENABLE_METRICS", "1")
    monkeypatch.setenv("BACKLOG_PROBE_SECONDS", "5")
    monkeypatch.setenv("WORKER_METRICS_HTTP", "0")
    captured = {}

    def fake_enable(celery_app_instance, *, broker_url, queue_names, backlog_interval_s):
        captured["queue_names"] = queue_names

    monkeypatch.setattr(metrics, "enable_celery_metrics", fake_enable)
    monkeypatch.setattr(
        metrics, "start_worker_metrics_http_if_enabled", lambda *args, **kwargs: None
    )
    from services.worker import celery_app

    monkeypatch.setattr(celery_app.settings, "QUEUE_NAMES", "ingest, priority")
    monkeypatch.setattr(celery_app.settings, "BROKER_URL", "redis://localhost/0")

    importlib.reload(celery_app)
    assert captured["queue_names"] == ["ingest", "priority"]


def test_record_etl_run_tracks_success_and_failure(monkeypatch):
    times = iter([1.0, 2.0, 3.0, 5.0])
    monkeypatch.setattr(metrics.time, "perf_counter", lambda: next(times))

    with metrics.record_etl_run("pipeline"):
        pass

    with pytest.raises(RuntimeError):
        with metrics.record_etl_run("pipeline"):
            raise RuntimeError("boom")

    runs = metrics.ETL_RUNS_TOTAL.collect()[0].samples
    success = next(sample for sample in runs if sample.labels["status"] == "success")
    failure = next(sample for sample in runs if sample.labels["status"] == "failed")
    assert success.value == 1.0
    assert failure.value == 1.0
    failures = metrics.ETL_FAILURES_TOTAL.collect()[0].samples
    assert any(sample.labels["reason"] == "RuntimeError" for sample in failures)


def test_record_etl_skip_and_retry_counts() -> None:
    metrics.ETL_RUNS_TOTAL.clear()
    metrics.ETL_RETRY_TOTAL.clear()
    metrics.record_etl_skip("demo")
    metrics.record_etl_retry("demo", "429")
    runs = metrics.ETL_RUNS_TOTAL.collect()[0].samples
    skip = next(sample for sample in runs if sample.labels["status"] == "skipped")
    assert skip.value == 1.0
    retries = metrics.ETL_RETRY_TOTAL.collect()[0].samples
    assert any(sample.labels["code"] == "429" for sample in retries)
