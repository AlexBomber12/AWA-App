from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Role(str, Enum):
    viewer = "viewer"
    ops = "ops"
    admin = "admin"

    @classmethod
    def from_claim(cls, value: str | None) -> Role | None:
        if not value:
            return None
        lowered = value.lower().strip()
        for role in cls:
            if role.value == lowered:
                return role
        return None


class UserCtx(BaseModel):
    sub: str = Field(..., description="Stable subject identifier for the authenticated user.")
    email: str | None = Field(default=None, description="Primary email address when available.")
    roles: list[Role] = Field(default_factory=list, description="Resolved application roles.")
    raw_claims: dict[str, Any] = Field(default_factory=dict, description="Original JWT claims.")

    @field_validator("roles", mode="before")
    @classmethod
    def _ensure_unique_roles(cls, value: Any) -> list[Role]:
        items = value or []
        roles: list[Role] = []
        seen: set[Role] = set()
        for item in items:
            if isinstance(item, Role):
                role = item
            else:
                role = Role.from_claim(str(item))
                if role is None:
                    continue
            if role not in seen:
                roles.append(role)
                seen.add(role)
        return roles

    @property
    def role_set(self) -> set[Role]:
        return set(self.roles)
