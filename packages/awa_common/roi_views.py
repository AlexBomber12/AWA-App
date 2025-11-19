from __future__ import annotations

import time
from typing import Final

from awa_common.settings import settings

DEFAULT_ROI_VIEW: Final[str] = "v_roi_full"
ALLOWED_ROI_VIEWS: Final[frozenset[str]] = frozenset(
    {
        "v_roi_full",
        "roi_view",
        "mat_v_roi_full",
        "test_roi_view",
    }
)
_CACHE_TTL_S = 30.0
_cached_name: str | None = None
_cached_at: float = 0.0


class InvalidROIViewError(ValueError):
    """Raised when roi-related SQL tries to use an unapproved view name."""


def _raw_roi_view_name(cfg) -> str:
    try:
        value = cfg.ROI_VIEW_NAME
    except Exception:
        value = None
    if isinstance(value, str) and value.strip():
        return value.strip()
    try:
        roi_cfg = getattr(cfg, "roi", None)
    except Exception:  # pragma: no cover - defensive
        roi_cfg = None
    if roi_cfg is not None:
        raw = getattr(roi_cfg, "view_name", DEFAULT_ROI_VIEW)
    else:
        raw = getattr(cfg, "view_name", DEFAULT_ROI_VIEW)
    return (raw or DEFAULT_ROI_VIEW).strip()


def _resolve_roi_view(cfg) -> str:
    name = _raw_roi_view_name(cfg) or DEFAULT_ROI_VIEW
    if name not in ALLOWED_ROI_VIEWS:
        allowed = ", ".join(sorted(ALLOWED_ROI_VIEWS))
        raise InvalidROIViewError(f"ROI view '{name}' is not allowed. Expected one of: {allowed}.")
    return name


def current_roi_view(cfg=settings, *, ttl_seconds: float = _CACHE_TTL_S) -> str:
    """Return the ROI view name using a short-lived cache to avoid env churn."""
    global _cached_name, _cached_at
    now = time.monotonic()
    if _cached_name and now - _cached_at <= ttl_seconds:
        return _cached_name
    resolved = _resolve_roi_view(cfg)
    _cached_name = resolved
    _cached_at = now
    return resolved


def clear_caches() -> None:
    """Reset cached ROI view state (used in tests)."""
    global _cached_name, _cached_at
    _cached_name = None
    _cached_at = 0.0


def quote_identifier(identifier: str) -> str:
    """Safely quote a schema-qualified identifier."""
    if not identifier:
        raise InvalidROIViewError("ROI view name cannot be empty.")
    parts = identifier.split(".")
    quoted_parts: list[str] = []
    for part in parts:
        if not part:
            raise InvalidROIViewError("ROI view name cannot contain empty segments.")
        quoted = part.replace('"', '""')
        quoted_parts.append(f'"{quoted}"')
    return ".".join(quoted_parts)


def get_quoted_roi_view() -> str:
    """Return the configured ROI view, quoted for SQL usage."""
    return quote_identifier(current_roi_view())


__all__ = [
    "ALLOWED_ROI_VIEWS",
    "DEFAULT_ROI_VIEW",
    "InvalidROIViewError",
    "clear_caches",
    "current_roi_view",
    "get_quoted_roi_view",
    "quote_identifier",
]
