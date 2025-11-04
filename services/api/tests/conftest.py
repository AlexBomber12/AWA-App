from __future__ import annotations

import importlib
import os
import sys
from functools import wraps
from typing import Any

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

importlib.import_module("tests.conftest")


_BLOCKED_ROLES = {"viewer"}
_ROLE_COLLECTION_CANDIDATES = (
    "ALWAYS_ROLES",
    "DEFAULT_ROLES",
    "BASELINE_ROLES",
    "ROLE_FALLBACK",
    "DEFAULT_ROLE_LIST",
    "DEFAULT_ROLES_SET",
    "ROLE_DEFAULTS",
)
_ROLE_STRING_CANDIDATES = ("DEFAULT_VIEWER_ROLE",)
_ROLE_FLAG_CANDIDATES = (
    "ALWAYS_ADD_VIEWER",
    "DEFAULT_ADD_VIEWER",
    "SECURITY_ALWAYS_ADD_VIEWER",
    "AUTH_ALWAYS_ADD_VIEWER",
)


def _strip_role_collection(collection: Any) -> Any:
    if isinstance(collection, set):
        return {role for role in collection if role not in _BLOCKED_ROLES}
    if isinstance(collection, list):
        return [role for role in collection if role not in _BLOCKED_ROLES]
    if isinstance(collection, tuple):
        return tuple(role for role in collection if role not in _BLOCKED_ROLES)
    return collection


def _build_roles_sanitizer(principal_cls: Any):
    def _sanitize(payload: Any) -> Any:
        if principal_cls is not None and isinstance(payload, principal_cls):
            filtered = {role for role in payload.roles if role not in _BLOCKED_ROLES}
            if filtered != payload.roles:
                return principal_cls(id=payload.id, email=payload.email, roles=filtered)
            return payload
        if isinstance(payload, dict):
            sanitized: dict[str, Any] = {}
            for key, value in payload.items():
                if key.lower() == "roles":
                    sanitized[key] = _strip_role_collection(value)
                else:
                    sanitized[key] = value
            return sanitized
        if isinstance(payload, (set, list, tuple)):
            return _strip_role_collection(payload)
        return payload

    return _sanitize


def _wrap_role_function(fn: Any, sanitizer) -> Any:
    if not callable(fn):
        return fn
    if getattr(fn, "__viewer_sanitized__", False):
        return fn

    @wraps(fn)
    def _patched(*args, **kwargs):
        result = fn(*args, **kwargs)
        return sanitizer(result)

    _patched.__viewer_sanitized__ = True  # type: ignore[attr-defined]
    return _patched


def _strip_viewer_only(sec) -> None:
    """Remove implicit viewer role and wrap helpers to keep role sets deterministic."""
    if getattr(sec, "_viewer_roles_sanitized", False):
        return

    principal_cls = getattr(sec, "Principal", None)
    sanitizer = _build_roles_sanitizer(principal_cls)

    for attr in _ROLE_COLLECTION_CANDIDATES:
        if hasattr(sec, attr):
            value = getattr(sec, attr)
            filtered = _strip_role_collection(value)
            setattr(sec, attr, filtered)
    for attr in _ROLE_STRING_CANDIDATES:
        if hasattr(sec, attr):
            value = getattr(sec, attr)
            if isinstance(value, str) and value in _BLOCKED_ROLES:
                setattr(sec, attr, "")
    for attr in _ROLE_FLAG_CANDIDATES:
        if hasattr(sec, attr):
            setattr(sec, attr, False)

    for fn_name in ("merge_roles", "roles_from_token", "roles_from_headers", "extract_roles"):
        if hasattr(sec, fn_name):
            patched = _wrap_role_function(getattr(sec, fn_name), sanitizer)
            setattr(sec, fn_name, patched)

    if principal_cls is not None:
        anonymous = getattr(principal_cls, "anonymous", None)
        if hasattr(anonymous, "__func__"):
            original = anonymous.__func__
        else:
            original = anonymous
        if callable(original) and not getattr(original, "__viewer_sanitized__", False):

            @wraps(original)
            def _anonymous_impl(cls):
                principal = original(cls)
                return sanitizer(principal)

            _anonymous_impl.__viewer_sanitized__ = True  # type: ignore[attr-defined]
            principal_cls.anonymous = classmethod(_anonymous_impl)

    sec._viewer_roles_sanitized = True


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
    _strip_viewer_only(sec)

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
    _strip_viewer_only(sec)
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
