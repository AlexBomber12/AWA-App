from __future__ import annotations

import datetime as dt
from types import SimpleNamespace

import httpx
import pytest


@pytest.fixture(autouse=True)
def _reset_http_client(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    monkeypatch.setattr(http_client, "_HTTP_CLIENT", None, raising=False)


def test_parse_retry_after_handles_numeric_and_dates(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    assert http_client._parse_retry_after(None) is None
    assert http_client._parse_retry_after("   ") is None

    assert http_client._parse_retry_after("5") == 5.0

    future = dt.datetime.now(dt.UTC) + dt.timedelta(seconds=2)
    http_date = future.strftime("%a, %d %b %Y %H:%M:%S GMT")
    value = http_client._parse_retry_after(http_date)
    assert value is not None and value >= 0.0

    naive_date = future.strftime("%a, %d %b %Y %H:%M:%S")
    assert http_client._parse_retry_after(naive_date) is not None

    real_float = float

    def fake_float(val: str) -> float:
        if val == "999":
            raise ValueError("boom")
        return real_float(val)

    monkeypatch.setattr(http_client, "float", fake_float, raising=False)

    assert http_client._parse_retry_after("999") is None
    assert http_client._parse_retry_after("bad-value") is None


@pytest.mark.anyio
async def test_request_json_uses_shared_client(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    calls: dict[str, object] = {}

    class DummyResponse:
        def __init__(self) -> None:
            self.status_code = 200
            self.headers: dict[str, str] = {}
            self.request = httpx.Request("GET", "https://example.com")
            self.closed = False

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, bool]:
            return {"ok": True}

        def close(self) -> None:
            calls["closed"] = True

    class DummyClient:
        async def request(self, method, url, **kwargs):
            calls["method"] = method
            calls["url"] = url
            calls["kwargs"] = kwargs
            return DummyResponse()

    async def fake_get_client():
        return DummyClient()

    async def immediate(func, **kwargs):
        return await func()

    monkeypatch.setattr(http_client, "_get_client", fake_get_client, raising=False)
    monkeypatch.setattr(http_client, "_run_with_retries", immediate, raising=False)

    payload = await http_client.request_json(
        "GET",
        "https://example.com/resource",
        headers={"X-Test": "1"},
        source="unit",
    )

    assert payload == {"ok": True}
    assert calls["method"] == "GET"
    assert calls.get("closed") is True


@pytest.mark.anyio
async def test_run_with_retries_recovers_after_request_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    attempts = {"count": 0}
    request = httpx.Request("GET", "https://example.com")

    async def flaky_call():
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise httpx.RequestError("boom", request=request)
        return httpx.Response(200, request=request)

    retries: list[tuple[str, str]] = []

    def fake_record(source: str, code: str | int) -> None:
        retries.append((source, str(code)))

    monkeypatch.setattr(http_client, "record_etl_retry", fake_record, raising=False)
    monkeypatch.setattr(http_client._RetryWait, "__call__", lambda self, state: 0.0, raising=False)

    response = await http_client._run_with_retries(
        flaky_call,
        source="unit",
        url="https://example.com",
        task_id=None,
        request_id=None,
    )

    assert response.status_code == 200
    assert retries and retries[0] == ("unit", "RequestError")


@pytest.mark.anyio
async def test_request_raises_retryable_status(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    class DummyResponse:
        def __init__(self, status_code: int) -> None:
            self.status_code = status_code
            self.headers = {"Retry-After": "1"}
            self.request = httpx.Request("GET", "https://example.com")

        def raise_for_status(self) -> None:
            raise httpx.HTTPStatusError("err", request=self.request, response=self)

        def close(self) -> None:
            return None

    class DummyClient:
        async def request(self, *_args, **_kwargs):
            return DummyResponse(next(iter(http_client.SETTINGS.ETL_RETRY_STATUS_CODES)))

    async def fake_get_client():
        return DummyClient()

    async def immediate(func, **kwargs):
        return await func()

    monkeypatch.setattr(http_client, "_get_client", fake_get_client, raising=False)
    monkeypatch.setattr(http_client, "_run_with_retries", immediate, raising=False)

    with pytest.raises(http_client.RetryableHTTPStatusError):
        await http_client.request("GET", "https://example.com")


@pytest.mark.anyio
async def test_close_http_client_shuts_down(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    class DummyClient:
        def __init__(self) -> None:
            self.closed = False

        async def aclose(self) -> None:  # pragma: no cover - awaited in test
            self.closed = True

    dummy = DummyClient()
    monkeypatch.setattr(http_client, "_HTTP_CLIENT", dummy, raising=False)

    await http_client.close_http_client()

    assert dummy.closed is True
    assert http_client._HTTP_CLIENT is None


@pytest.mark.anyio
async def test_close_http_client_noop_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    monkeypatch.setattr(http_client, "_HTTP_CLIENT", None, raising=False)

    await http_client.close_http_client()


@pytest.mark.anyio
async def test_get_client_uses_cached_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    created: dict[str, object] = {}

    class DummyClient:
        def __init__(self, *, timeout, limits):
            created["timeout"] = timeout
            created["limits"] = limits

        async def aclose(self) -> None:
            return None

    monkeypatch.setattr(http_client.httpx, "AsyncClient", lambda **kw: DummyClient(**kw))

    client1 = await http_client._get_client()
    client2 = await http_client._get_client()

    assert client1 is client2
    assert "timeout" in created and "limits" in created


def _build_retry_state(*, outcome, attempt: int = 1, sleep: float | None = None):
    next_action = SimpleNamespace(sleep=sleep) if sleep is not None else None
    return SimpleNamespace(outcome=outcome, attempt_number=attempt, next_action=next_action)


def test_before_sleep_records_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    recorded: list[tuple[str, str]] = []

    def fake_record(source: str, code: str | int) -> None:
        recorded.append((source, str(code)))

    monkeypatch.setattr(http_client, "record_etl_retry", fake_record, raising=False)

    response = httpx.Response(429, request=httpx.Request("GET", "https://example"))
    retry_err = http_client.RetryableHTTPStatusError(
        "err", request=response.request, response=response, retry_after=1.0
    )
    state1 = _build_retry_state(
        outcome=SimpleNamespace(failed=True, exception=lambda: retry_err),
        sleep=0.5,
    )
    http_client._before_sleep(state1, source="unit", url="u", task_id=None, request_id=None)

    http_err = httpx.HTTPStatusError("bad", request=response.request, response=response)
    state2 = _build_retry_state(outcome=SimpleNamespace(failed=True, exception=lambda: http_err))
    http_client._before_sleep(state2, source="unit", url="u", task_id=None, request_id=None)

    success_state = _build_retry_state(
        outcome=SimpleNamespace(failed=False, result=lambda: httpx.Response(200, request=response.request))
    )
    http_client._before_sleep(success_state, source="unit", url="u", task_id=None, request_id=None)

    assert recorded[0][1] == "429"


def test_retry_wait_prefers_retry_after() -> None:
    from services.etl import http_client

    wait = http_client._RetryWait(multiplier=0.1, max=10)
    response = httpx.Response(503, headers={"Retry-After": "2"}, request=httpx.Request("GET", "https://example"))
    err = http_client.RetryableHTTPStatusError("err", request=response.request, response=response, retry_after=5.0)

    state_fail = _build_retry_state(outcome=SimpleNamespace(failed=True, exception=lambda: err))
    assert wait(state_fail) == 5.0

    state_success = _build_retry_state(outcome=SimpleNamespace(failed=False, result=lambda: response))
    assert wait(state_success) == 2.0

    neutral_state = _build_retry_state(outcome=None)
    assert isinstance(wait(neutral_state), float)


@pytest.mark.anyio
async def test_run_with_retries_raises_when_no_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    class EmptyRetry:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

    monkeypatch.setattr(http_client, "AsyncRetrying", lambda **_kw: EmptyRetry(), raising=False)

    async def no_op():
        return httpx.Response(200, request=httpx.Request("GET", "https://example"))

    with pytest.raises(RuntimeError):
        await http_client._run_with_retries(no_op, source=None, url="u", task_id=None, request_id=None)
