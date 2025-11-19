import pytest
from fastapi import HTTPException

from services.worker.repricer.app import main as repricer_main


@pytest.mark.asyncio
async def test_fetch_inputs_wraps_invalid_roi(monkeypatch):
    async def fake_execute(stmt, params):
        return type(
            "Result",
            (),
            {"mappings": lambda self: type("M", (), {"first": lambda self: None})()},
        )()

    class DummySession:
        async def execute(self, stmt, params):
            return await fake_execute(stmt, params)

    def _bad_view():
        raise repricer_main.InvalidROIViewError("bad-view")

    monkeypatch.setattr(repricer_main, "current_roi_view", _bad_view)
    with pytest.raises(HTTPException) as exc:
        await repricer_main._fetch_inputs(DummySession(), "ASIN123")
    assert exc.value.status_code == 400
