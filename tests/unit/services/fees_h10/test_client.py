from __future__ import annotations

import pytest

from services.fees_h10 import client


@pytest.mark.anyio
async def test_init_http_client_force_recreates(monkeypatch: pytest.MonkeyPatch) -> None:
    closed = {"count": 0}

    class FakeClient:
        def __init__(self, *, integration: str, base_url: str, total_timeout_s: float, max_retries: int):  # noqa: D401
            self.integration = integration
            self.base_url = base_url
            self.total_timeout_s = total_timeout_s
            self.max_retries = max_retries
            closed["created"] = closed.get("created", 0) + 1
            self.closed = False

        async def aclose(self) -> None:
            self.closed = True
            closed["count"] += 1

    monkeypatch.setattr(client, "AsyncHTTPClient", FakeClient)
    # Seed an existing client so the force branch triggers a close + recreate.
    client._HTTP_CLIENT = FakeClient(integration="old", base_url="http://old", total_timeout_s=1, max_retries=1)  # type: ignore[attr-defined]
    client._HTTP_CLIENT_CONFIG = ("http://old", 1.0, 1)  # type: ignore[attr-defined]

    new_client = await client.init_http_client(force=True)

    assert isinstance(new_client, FakeClient)
    assert closed["count"] == 1
    assert closed.get("created", 0) == 2
    assert client._HTTP_CLIENT is new_client  # type: ignore[attr-defined]
    client._HTTP_CLIENT = None  # type: ignore[attr-defined]
