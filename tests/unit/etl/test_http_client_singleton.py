from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest


@pytest.mark.anyio
async def test_fetch_json_closes_response_and_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    events: dict[str, list[tuple[str, dict[str, object]]]] = {"info": [], "warning": []}

    responses: list = []

    class DummyResponse:
        def __init__(self) -> None:
            self.status_code = 200
            self.headers: dict[str, str] = {}
            self.closed = False

        def json(self) -> dict[str, bool]:
            return {"ok": True}

        def close(self) -> None:
            self.closed = True

    async def fake_request(*_args, **_kwargs):
        resp = DummyResponse()
        responses.append(resp)
        return resp

    monkeypatch.setattr(http_client, "request", fake_request, raising=False)
    monkeypatch.setattr(
        http_client,
        "logger",
        SimpleNamespace(
            info=lambda event, **kw: events["info"].append((event, kw)),
            warning=lambda *args, **kwargs: events["warning"].append((args[0], kwargs)),
        ),
        raising=False,
    )

    result = await http_client.fetch_json("GET", "https://example.com", source="unit", request_id="req-1")

    assert result == {"ok": True}
    assert responses and responses[0].closed is True
    assert events["info"]
    assert events["info"][0][0] == "etl_http.request_completed"


@pytest.mark.anyio
async def test_fetch_json_logs_warning_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    events: list[dict[str, object]] = []
    request = httpx.Request("GET", "https://example.com")

    async def boom(*_args, **_kwargs):
        raise httpx.HTTPStatusError("bad", request=request, response=httpx.Response(500, request=request))

    monkeypatch.setattr(http_client, "request", boom, raising=False)
    monkeypatch.setattr(
        http_client,
        "logger",
        SimpleNamespace(
            warning=lambda event, **kw: events.append({"event": event, **kw}),
        ),
        raising=False,
    )

    with pytest.raises(httpx.HTTPStatusError):
        await http_client.fetch_json("GET", "https://example.com", source="unit")

    assert events
    assert events[0]["event"] == "etl_http.request_failed"


@pytest.mark.anyio
async def test_get_client_delegates_to_private(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.etl import http_client

    called = {}

    async def fake_get():
        called["hit"] = True
        return "client"

    monkeypatch.setattr(http_client, "_get_client", fake_get, raising=False)
    assert await http_client.get_client() == "client"
    assert called["hit"] is True
