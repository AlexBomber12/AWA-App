from __future__ import annotations

import os

DEFAULT_ROI_VIEW = "v_roi_full"
ALLOWED_ROI_VIEWS: frozenset[str] = frozenset(
    {
        "v_roi_full",
        "roi_view",
        "mat_v_roi_full",
        "test_roi_view",
    }
)


class InvalidROIViewError(ValueError):
    """Raised when roi-related SQL tries to use an unapproved view name."""


def _raw_roi_view_name() -> str:
    return os.getenv("ROI_VIEW_NAME", DEFAULT_ROI_VIEW).strip()


def get_roi_view_name() -> str:
    """Return a whitelisted ROI view name from the environment."""
    name = _raw_roi_view_name() or DEFAULT_ROI_VIEW
    if name not in ALLOWED_ROI_VIEWS:
        allowed = ", ".join(sorted(ALLOWED_ROI_VIEWS))
        raise InvalidROIViewError(f"ROI view '{name}' is not allowed. Expected one of: {allowed}.")
    return name


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
    return quote_identifier(get_roi_view_name())


__all__ = [
    "ALLOWED_ROI_VIEWS",
    "DEFAULT_ROI_VIEW",
    "InvalidROIViewError",
    "get_roi_view_name",
    "get_quoted_roi_view",
    "quote_identifier",
]
