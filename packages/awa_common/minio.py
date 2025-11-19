from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:  # pragma: no cover - import-time typing helper
    from botocore.client import BaseClient
    from botocore.config import Config
else:  # pragma: no cover - runtime fallback when botocore is absent
    BaseClient = Any
    Config = Any

from .configuration import S3Settings
from .settings import settings

logger = structlog.get_logger(__name__)


def _s3_settings() -> S3Settings:
    s3_cfg = getattr(settings, "s3", None)
    if s3_cfg is None:
        message = "S3/MinIO configuration is missing from awa_common.settings"
        logger.error("minio.configuration_missing")
        raise RuntimeError(message)
    return s3_cfg


def get_bucket_name() -> str:
    """Return the configured default MinIO/S3 bucket."""

    return _s3_settings().bucket


def get_s3_client_kwargs(*, secure_override: bool | None = None) -> dict[str, Any]:
    """Return client keyword arguments for boto3/aioboto3 based on shared settings."""

    return _s3_settings().client_kwargs(secure_override=secure_override)


def create_boto3_client(*, config: Config | None = None, **overrides: Any) -> BaseClient:
    """Instantiate a boto3 S3 client that respects the shared configuration."""

    try:
        import boto3
    except Exception as exc:  # pragma: no cover - import failure handled by caller
        raise RuntimeError("boto3 is required to create an S3 client") from exc

    client_kwargs = get_s3_client_kwargs()
    if overrides:
        client_kwargs.update(overrides)
    return boto3.client("s3", config=config, **client_kwargs)
