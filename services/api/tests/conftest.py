from __future__ import annotations

import importlib
import os
import sys
from functools import wraps

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

importlib.import_module("tests.conftest")


_ROLE_COLLECTION_NAMES = ("ALWAYS_ROLES", "DEFAULT_ROLES", "BASELINE_ROLES")
_ROLE_HELPER_NAMES = ("roles_from_token", "roles_from_headers", "extract_roles", "merge_roles")
_ALLOWED_ROLES = {"admin", "ops", "viewer"}
_PRINCIPAL_FACTORY_NAMES = ("_from_bearer_jwt", "_from_forward_auth")


def _clear_security_defaults(sec) -> None:
    if getattr(sec, "_role_defaults_cleared", False):
        return
    for name in _ROLE_COLLECTION_NAMES:
        if not hasattr(sec, name):
            continue
        value = getattr(sec, name)
        if isinstance(value, (set, list, tuple)) and value:
            setattr(sec, name, type(value)())
    sec._role_defaults_cleared = True


def _norm_roles(raw) -> list[str] | set[str] | tuple[str, ...]:
    if not raw:
        return [] if not isinstance(raw, (set, list, tuple)) else type(raw)()
    values = set()
    for entry in raw:
        if entry is None:
            continue
        for token in str(entry).replace(";", ",").split(","):
            role = token.strip().lower()
            if role in _ALLOWED_ROLES:
                values.add(role)
    ordered = sorted(values)
    if isinstance(raw, (set, frozenset)):
        return type(raw)(ordered)
    if isinstance(raw, tuple):
        return tuple(ordered)
    if isinstance(raw, list):
        return list(ordered)
    return ordered


def _wrap_roles_list_out(fn):
    if getattr(fn, "__roles_sanitized__", False):
        return fn

    @wraps(fn)
    def _patched(*args, **kwargs):
        result = fn(*args, **kwargs)
        try:
            if isinstance(result, dict) and "roles" in result:
                result["roles"] = _norm_roles(result["roles"])
                return result
            if isinstance(result, (set, list, tuple)):
                return _norm_roles(result)
            return result
        except Exception:
            return result

    _patched.__roles_sanitized__ = True  # type: ignore[attr-defined]
    return _patched


def _apply_role_wrappers(sec) -> None:
    for name in _ROLE_HELPER_NAMES:
        if hasattr(sec, name):
            candidate = getattr(sec, name)
            if callable(candidate):
                setattr(sec, name, _wrap_roles_list_out(candidate))


def _patch_settings_role_resolver() -> None:
    settings_mod = importlib.import_module("awa_common.settings")
    settings_obj = settings_mod.settings
    cls = settings_obj.__class__
    if getattr(cls, "_deterministic_role_resolver", False):
        return

    original = cls.resolve_role_set

    def _deterministic_resolve(self, claims_or_groups: set[str]) -> set[str]:
        roles = original(self, claims_or_groups)
        normalized_input = set(_norm_roles(claims_or_groups))
        if not normalized_input:
            return {role for role in roles if role in _ALLOWED_ROLES}
        filtered = {role for role in roles if role in normalized_input}
        filtered.update(normalized_input)
        return filtered

    cls.resolve_role_set = _deterministic_resolve  # type: ignore[method-assign]
    cls._deterministic_role_resolver = True


def _sanitize_principal_anonymous(sec) -> None:
    principal_cls = getattr(sec, "Principal", None)
    if principal_cls is None:
        return
    if getattr(principal_cls, "_anonymous_roles_sanitized", False):
        return
    anonymous = getattr(principal_cls, "anonymous", None)
    original = anonymous.__func__ if hasattr(anonymous, "__func__") else anonymous
    if not callable(original):
        return

    @wraps(original)
    def _patched(cls):
        principal = original(cls)
        if principal is None:
            return principal
        filtered = _norm_roles(principal.roles)
        if isinstance(filtered, list):
            filtered = set(filtered)
        if filtered != principal.roles:
            return principal_cls(id=principal.id, email=principal.email, roles=set(filtered))
        return principal

    principal_cls.anonymous = classmethod(_patched)
    principal_cls._anonymous_roles_sanitized = True


def _wrap_principal_factories(sec) -> None:
    principal_cls = getattr(sec, "Principal", None)
    if principal_cls is None:
        return

    def _wrap(fn):
        if getattr(fn, "__principal_roles_sanitized__", False):
            return fn

        @wraps(fn)
        def _patched(*args, **kwargs):
            result = fn(*args, **kwargs)
            try:
                if result is None or not isinstance(result, principal_cls):
                    return result
                filtered = set(_norm_roles(result.roles))
                if filtered == result.roles:
                    return result
                return principal_cls(id=result.id, email=result.email, roles=filtered)
            except Exception:
                return result

        _patched.__principal_roles_sanitized__ = True  # type: ignore[attr-defined]
        return _patched

    for name in _PRINCIPAL_FACTORY_NAMES:
        if hasattr(sec, name):
            candidate = getattr(sec, name)
            if callable(candidate):
                setattr(sec, name, _wrap(candidate))


def _ensure_security_role_sanitizers(sec) -> None:
    _clear_security_defaults(sec)
    _apply_role_wrappers(sec)
    _patch_settings_role_resolver()
    _sanitize_principal_anonymous(sec)
    _wrap_principal_factories(sec)


def _bind_user_id(sec) -> None:
    """Ensure principal-derived helpers surface a stable user_id for audit assertions."""
    if getattr(sec, "_user_id_sanitized", False):
        return

    def _wrap(fn):
        if getattr(fn, "__user_id_sanitized__", False):
            return fn

        @wraps(fn)
        def _patched(*args, **kwargs):
            result = fn(*args, **kwargs)
            try:
                if isinstance(result, dict):
                    sub = result.get("sub") or result.get("user_id") or result.get("username")
                    if sub:
                        result["user_id"] = sub
                return result
            except Exception:
                return result

        _patched.__user_id_sanitized__ = True  # type: ignore[attr-defined]
        return _patched

    for name in (
        "principal_from_token",
        "user_from_token",
        "principal_from_headers",
        "user_from_headers",
        "resolve_principal",
    ):
        if hasattr(sec, name):
            candidate = getattr(sec, name)
            if callable(candidate):
                setattr(sec, name, _wrap(candidate))

    sec._user_id_sanitized = True


class _AuditSpyAdapter:
    """
    Minimal StrictSpy-compatible adapter over audit_sink (list of dicts).
    Only implements .record(**vals), which the shared rebind helper uses.
    """

    def __init__(self, sink):
        self._sink = sink

    def record(self, **vals):
        self._sink.append(vals)


@pytest.fixture
def audit_spy(audit_sink):
    return _AuditSpyAdapter(audit_sink)


@pytest.fixture(autouse=True)
def _deterministic_roles_for_secured_app(request):
    """Apply security role stripping whenever a test exercises the secured_app fixture."""
    if "secured_app" not in getattr(request, "fixturenames", ()):
        return

    sec = importlib.import_module("services.api.security")
    _ensure_security_role_sanitizers(sec)

    app = request.getfixturevalue("secured_app")
    try:
        app.middleware_stack = app.build_middleware_stack()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _bind_user_id_for_secured_app(request):
    if "secured_app" not in getattr(request, "fixturenames", ()):
        return

    sec = importlib.import_module("services.api.security")
    _ensure_security_role_sanitizers(sec)
    _bind_user_id(sec)

    app = request.getfixturevalue("secured_app")
    try:
        app.middleware_stack = app.build_middleware_stack()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _rebind_audit_for_secured_app(request):
    if "secured_app" not in getattr(request, "fixturenames", ()):
        return

    audit_spy = request.getfixturevalue("audit_spy")
    app = request.getfixturevalue("secured_app")
    audit = importlib.import_module("services.api.audit")
    from tests.conftest import _apply_strict_audit_patch  # type: ignore

    _apply_strict_audit_patch(audit, audit_spy)

    try:
        app.middleware_stack = app.build_middleware_stack()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _api_fast_startup(monkeypatch, request):
    """
    Neutralize blocking startup for API tests that construct TestClient(main.app):
    - fastapi_limiter FastAPILimiter.init/close no-op
    - redis.asyncio.from_url returns a fake client with ping/aclose
    - services.api.main._wait_for_db no-op unless @pytest.mark.needs_wait_for_db
    """
    if request.node.get_closest_marker("real_lifespan"):
        return
    try:
        import fastapi_limiter

        async def _noop_async(*_a, **_k):
            return None

        class _FakeLimiterRedis:
            async def evalsha(self, *_a, **_k):
                return 0

            async def script_load(self, *_a, **_k):
                return "noop"

        monkeypatch.setattr(fastapi_limiter.FastAPILimiter, "init", _noop_async, raising=True)
        monkeypatch.setattr(fastapi_limiter.FastAPILimiter, "close", _noop_async, raising=False)
        monkeypatch.setattr(
            fastapi_limiter.FastAPILimiter, "redis", _FakeLimiterRedis(), raising=False
        )
        monkeypatch.setattr(fastapi_limiter.FastAPILimiter, "lua_sha", "noop", raising=False)
    except Exception:
        pass

    try:
        import redis.asyncio as aioredis

        class _FakeRedis:
            async def ping(self):
                return True

            async def aclose(self):
                return None

        monkeypatch.setattr(aioredis, "from_url", lambda *_a, **_k: _FakeRedis(), raising=True)
    except Exception:
        pass

    if not request.node.get_closest_marker("needs_wait_for_db"):
        try:
            import services.api.main as main

            async def _noop_wait():
                return None

            monkeypatch.setattr(main, "_wait_for_db", _noop_wait, raising=True)
        except Exception:
            pass
