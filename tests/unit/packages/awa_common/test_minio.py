from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from awa_common import minio as minio_module
from awa_common.settings import Settings


def _fresh_settings(monkeypatch, **env: str) -> Settings:
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    cfg = Settings()
    monkeypatch.setattr(minio_module, "settings", cfg)
    return cfg


def test_get_s3_client_kwargs_from_settings(monkeypatch):
    _fresh_settings(
        monkeypatch,
        MINIO_ENDPOINT="minio.service.internal:9000",
        MINIO_SECURE="1",
        MINIO_ACCESS_KEY="key123",
        MINIO_SECRET_KEY="secret456",
        AWS_REGION="us-west-2",
    )

    kwargs = minio_module.get_s3_client_kwargs()
    assert kwargs["endpoint_url"] == "https://minio.service.internal:9000"
    assert kwargs["aws_access_key_id"] == "key123"
    assert kwargs["aws_secret_access_key"] == "secret456"
    assert kwargs["region_name"] == "us-west-2"


def test_get_s3_client_kwargs_preserves_custom_endpoint(monkeypatch):
    _fresh_settings(
        monkeypatch,
        MINIO_ENDPOINT="https://storage.example.com:9443",
        MINIO_SECURE="0",
    )

    kwargs = minio_module.get_s3_client_kwargs()
    assert kwargs["endpoint_url"] == "https://storage.example.com:9443"


def test_missing_s3_settings_raise(monkeypatch):
    monkeypatch.setattr(minio_module, "settings", SimpleNamespace(s3=None))
    with pytest.raises(RuntimeError):
        minio_module.get_bucket_name()


def test_create_boto3_client_uses_shared_kwargs(monkeypatch):
    _fresh_settings(
        monkeypatch,
        MINIO_ENDPOINT="minio:9000",
        MINIO_ACCESS_KEY="ak",
        MINIO_SECRET_KEY="sk",
        AWS_REGION="us-east-2",
    )
    captured: dict[str, object] = {}

    class DummyClient:
        pass

    def fake_client(service, *, config=None, **kwargs):
        captured["service"] = service
        captured["config"] = config
        captured["kwargs"] = kwargs
        return DummyClient()

    monkeypatch.setitem(sys.modules, "boto3", SimpleNamespace(client=fake_client))

    sentinel = object()
    client = minio_module.create_boto3_client(config=sentinel)
    assert isinstance(client, DummyClient)
    assert captured["service"] == "s3"
    assert captured["config"] is sentinel
    assert captured["kwargs"]["endpoint_url"].startswith("http://")
