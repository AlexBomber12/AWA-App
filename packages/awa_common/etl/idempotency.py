from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import blake2b
from pathlib import Path
from typing import Any

STABLE_REMOTE_KEYS = ("etag", "last_modified", "content_length", "content_md5")


@dataclass(frozen=True)
class _RemoteFingerprint:
    items: tuple[tuple[str, str], ...]

    def as_bytes(self) -> bytes:
        return json.dumps(self.items, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _blake_digest(payload: bytes) -> str:
    digest = blake2b(payload, digest_size=16)
    return f"b2:{digest.hexdigest()}"


def _normalise_remote_meta(remote_meta: dict[str, Any]) -> _RemoteFingerprint | None:
    normalised_source = {str(k).lower().replace("-", "_"): v for k, v in remote_meta.items()}
    candidates: list[tuple[str, str]] = []
    for key in STABLE_REMOTE_KEYS:
        value = normalised_source.get(key)
        if value is None:
            continue
        if isinstance(value, int | float):
            text = str(value)
        else:
            text = str(value).strip()
        if not text:
            continue
        candidates.append((key, text))
    if not candidates:
        return None
    candidates.sort()
    return _RemoteFingerprint(tuple(candidates))


def compute_idempotency_key(
    *,
    content: bytes | None = None,
    path: Path | None = None,
    remote_meta: dict[str, Any] | None = None,
) -> str:
    """Derive a deterministic key using remote metadata, file stats, or content hash."""

    if remote_meta:
        fingerprint = _normalise_remote_meta(remote_meta)
        if fingerprint is not None:
            return _blake_digest(fingerprint.as_bytes())

    if path is not None:
        stat_result = path.stat()
        payload = json.dumps(
            {
                "name": path.name,
                "size": stat_result.st_size,
                "mtime_ns": int(stat_result.st_mtime_ns),
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return _blake_digest(payload)

    if content is not None:
        return _blake_digest(content)

    raise ValueError("Must provide remote_meta, path, or content to compute idempotency key.")


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def build_payload_meta(
    *,
    path: Path | None = None,
    remote_meta: dict[str, Any] | None = None,
    source_url: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Aggregate payload metadata for persistence."""

    meta: dict[str, Any] = {}
    if path is not None:
        stat_result = path.stat()
        meta["filename"] = path.name
        meta["size_bytes"] = stat_result.st_size
        meta["mtime_epoch"] = int(stat_result.st_mtime)
    if remote_meta:
        fingerprint = _normalise_remote_meta(remote_meta) or _RemoteFingerprint(tuple())
        for key, value in fingerprint.items:
            meta[key] = value
        for raw_key in ("etag", "last_modified", "content_length", "content_md5"):
            normalised = _safe_str(remote_meta.get(raw_key)) or _safe_str(remote_meta.get(raw_key.replace("_", "-")))
            if normalised:
                meta.setdefault(raw_key, normalised)
    if source_url:
        meta["source_url"] = source_url
    if extra:
        meta.update(extra)
    return meta
