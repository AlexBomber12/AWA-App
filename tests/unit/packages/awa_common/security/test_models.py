from __future__ import annotations

from awa_common.security.models import Role, UserCtx


def test_role_enum_members():
    assert {role.value for role in Role} == {"viewer", "ops", "admin"}


def test_user_ctx_round_trip_preserves_fields():
    original = UserCtx(
        sub="subject-1",
        email="user@example.com",
        roles=[Role.viewer],
        raw_claims={"sub": "subject-1", "custom": "value"},
    )

    payload = original.model_dump()
    restored = UserCtx.model_validate_json(original.model_dump_json())

    assert payload["sub"] == "subject-1"
    assert payload["email"] == "user@example.com"
    assert payload["roles"] == [Role.viewer]
    assert payload["raw_claims"] == {"sub": "subject-1", "custom": "value"}
    assert restored == original


def test_user_ctx_filters_unknown_roles_and_deduplicates():
    user = UserCtx(
        sub="subject-2",
        email=None,
        roles=["VIEWER", Role.viewer, "admin", "unknown-role", "ops", "ops"],
        raw_claims={"roles": ["VIEWER", "admin", "unknown-role", "ops", "ops"]},
    )

    assert user.roles == [Role.viewer, Role.admin, Role.ops]
    assert user.role_set == {Role.viewer, Role.admin, Role.ops}
