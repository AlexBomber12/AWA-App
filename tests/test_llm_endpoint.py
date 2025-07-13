from fastapi.testclient import TestClient
import subprocess
from services.llm_server import app as llm_app

client = TestClient(llm_app.app)


def test_llm(monkeypatch):
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: b"ok")
    r = client.post("/llm", json={"prompt": "Hello", "max_tokens": 8})
    assert r.status_code == 200
