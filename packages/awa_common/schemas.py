from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class BaseStrictModel(BaseModel):
    """Base model enforcing strict validation and trimmed string inputs."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        coerce_numbers_to_str=False,
        validate_default=True,
        strict=True,
    )


__all__ = ["BaseStrictModel"]
