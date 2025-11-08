from __future__ import annotations

import pytest

from services.logistics_etl import client


@pytest.mark.integration
def test_unsupported_format_error_includes_diagnostics() -> None:
    raw = b"\x00\x01\x02binary-data"
    meta = {"content_type": "application/octet-stream"}

    with pytest.raises(client.UnsupportedFileFormatError) as exc:
        client._parse_rows("s3://bucket/file.bin", raw, meta)

    message = str(exc.value)
    assert "application/octet-stream" in message
    assert "binary-data" not in message  # ensure hex output
