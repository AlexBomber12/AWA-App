from __future__ import annotations

import os
from typing import Any

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def _coerce(
    name: str,
    parser,
    default: Any,
    raw: str | None,
) -> Any:
    if raw is None or raw.strip() == "":
        if default is None:
            raise ValueError(f"Environment variable {name} is required")
        return default
    try:
        return parser(raw)
    except ValueError as err:
        if default is None:
            raise ValueError(f"Environment variable {name} has invalid value {raw!r}") from err
        return default


def _apply_bounds(name: str, value: float | int, minimum: float | int | None, maximum: float | int | None) -> Any:
    if minimum is not None and value < minimum:
        raise ValueError(f"Environment variable {name} must be >= {minimum}, got {value}")
    if maximum is not None and value > maximum:
        raise ValueError(f"Environment variable {name} must be <= {maximum}, got {value}")
    return value


def env_int(name: str, default: int | None = None, *, min: int | None = None, max: int | None = None) -> int:
    """Read an integer environment variable with optional bounds enforcement."""

    raw = os.getenv(name)
    value = _coerce(name, int, default, raw)
    return int(_apply_bounds(name, int(value), min, max))


def env_float(name: str, default: float | None = None, *, min: float | None = None, max: float | None = None) -> float:
    """Read a float environment variable with optional bounds enforcement."""

    raw = os.getenv(name)
    value = float(_coerce(name, float, default, raw))
    return float(_apply_bounds(name, value, min, max))


def env_bool(name: str, default: bool | None = None) -> bool:
    """Parse a boolean environment variable supporting several truthy/falsey forms."""

    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        if default is None:
            raise ValueError(f"Environment variable {name} is required")
        return default
    value = raw.strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    if default is not None:
        return default
    raise ValueError(f"Environment variable {name} must be one of {sorted(_TRUE_VALUES | _FALSE_VALUES)}")


def env_str(name: str, default: str | None = None, *, strip: bool = True) -> str | None:
    """Return the raw environment value or ``default`` when unset."""

    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip() if strip else raw


__all__ = ["env_bool", "env_float", "env_int", "env_str"]
