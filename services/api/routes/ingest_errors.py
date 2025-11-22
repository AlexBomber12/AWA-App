"""Backwards-compatible wrappers for ingest error handling."""

from services.api.ingest_utils import (
    ApiError as IngestRequestError,
    api_error_response as ingest_error_response,
    respond_with_ingest_error,
)

__all__ = ["IngestRequestError", "ingest_error_response", "respond_with_ingest_error"]
