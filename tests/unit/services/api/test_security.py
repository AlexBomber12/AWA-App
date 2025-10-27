import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials

from services.api import security


def test_require_basic_auth_accepts_valid_credentials(monkeypatch):
    monkeypatch.setenv("API_BASIC_USER", "user")
    monkeypatch.setenv("API_BASIC_PASS", "pass")
    creds = HTTPBasicCredentials(username="user", password="pass")
    assert security.require_basic_auth(creds) is None


def test_require_basic_auth_rejects_invalid_credentials(monkeypatch):
    monkeypatch.setenv("API_BASIC_USER", "user")
    monkeypatch.setenv("API_BASIC_PASS", "pass")
    creds = HTTPBasicCredentials(username="bad", password="creds")
    with pytest.raises(HTTPException) as excinfo:
        security.require_basic_auth(creds)
    assert excinfo.value.status_code == 401
