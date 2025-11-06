from __future__ import annotations

import json
import os
import time
from pathlib import Path

from awa_common.etl import idempotency


def test_compute_idempotency_key_remote_meta_consistent() -> None:
    meta = {
        "ETag": '"abc"',
        "Last-Modified": "Wed, 21 Oct 2015 07:28:00 GMT",
        "Content-Length": "123",
    }
    key1 = idempotency.compute_idempotency_key(remote_meta=meta)
    key2 = idempotency.compute_idempotency_key(
        remote_meta={"etag": '"abc"', "content_length": 123, "last_modified": meta["Last-Modified"]}
    )
    assert key1 == key2


def test_compute_idempotency_key_remote_meta_varies() -> None:
    meta = {"etag": '"abc"', "content_length": "10"}
    key1 = idempotency.compute_idempotency_key(remote_meta=meta)
    key2 = idempotency.compute_idempotency_key(remote_meta={**meta, "content_length": "11"})
    assert key1 != key2


def test_compute_idempotency_key_path_changes(tmp_path: Path) -> None:
    file_path = tmp_path / "data.json"
    file_path.write_text(json.dumps({"value": 1}))
    key1 = idempotency.compute_idempotency_key(path=file_path)
    time.sleep(0.01)
    file_path.write_text(json.dumps({"value": 2}))
    stat = file_path.stat()
    os.utime(file_path, (stat.st_atime, stat.st_mtime + 5))
    key2 = idempotency.compute_idempotency_key(path=file_path)
    assert key1 != key2


def test_compute_idempotency_key_content_bytes() -> None:
    payload = b"hello-world"
    key1 = idempotency.compute_idempotency_key(content=payload)
    key2 = idempotency.compute_idempotency_key(content=b"hello-world")
    assert key1 == key2


def test_build_payload_meta_combines_sources(tmp_path: Path) -> None:
    file_path = tmp_path / "payload.bin"
    file_path.write_bytes(b"payload")
    meta = idempotency.build_payload_meta(
        path=file_path,
        remote_meta={"ETag": '"abc123"'},
        source_url="https://example.com/file",
        extra={"mode": "test"},
    )
    assert meta["filename"] == "payload.bin"
    assert meta["mode"] == "test"
    assert meta["etag"] == '"abc123"'
    assert meta["source_url"] == "https://example.com/file"


def test_build_payload_meta_handles_header_variants() -> None:
    meta = idempotency.build_payload_meta(
        remote_meta={"last-modified": "Mon", "content-md5": "deadbeef"}, extra={}
    )
    assert meta["last_modified"] == "Mon"
    assert meta["content_md5"] == "deadbeef"
