from __future__ import annotations

import re
import unicodedata
from pathlib import Path

ALLOWED_UPLOAD_EXTENSIONS = (".csv", ".csv.gz", ".xlsx", ".xls")
_INVALID_CHAR_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")
_MAX_FILENAME_LENGTH = 128


def sanitize_upload_name(name: str) -> str:
    """
    Normalise user-supplied upload filenames, rejecting traversal attempts and unsupported suffixes.
    """

    if not name or not isinstance(name, str):
        raise ValueError("Filename is required")

    normalized = unicodedata.normalize("NFKC", name)
    normalized = normalized.replace("\\", "/")
    if normalized.startswith("/"):
        raise ValueError("Absolute paths are not allowed")
    parts = [segment for segment in normalized.split("/") if segment]
    if any(part == ".." for part in parts):
        raise ValueError("Path traversal is not allowed")
    candidate = Path(normalized).name.strip()
    if not candidate:
        raise ValueError("Filename is empty after sanitisation")
    if candidate.startswith("."):
        raise ValueError("Hidden files are not allowed")

    ext = _extract_extension(candidate)
    base = candidate[: -len(ext)] if ext else candidate
    cleaned = _INVALID_CHAR_PATTERN.sub("_", base).strip("._")
    cleaned = re.sub(r"_+", "_", cleaned)
    if not cleaned:
        cleaned = "upload"

    if len(cleaned) > _MAX_FILENAME_LENGTH:
        cleaned = cleaned[:_MAX_FILENAME_LENGTH]

    sanitized = f"{cleaned}{ext}"
    if len(sanitized) > _MAX_FILENAME_LENGTH:
        sanitized = f"{cleaned[: _MAX_FILENAME_LENGTH - len(ext)]}{ext}"

    return sanitized


def _extract_extension(candidate: str) -> str:
    lowered = candidate.lower()
    if lowered.endswith(".csv.gz"):
        return ".csv.gz"
    suffix = Path(lowered).suffix
    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {suffix or 'none'}")
    return suffix


__all__ = ["sanitize_upload_name", "ALLOWED_UPLOAD_EXTENSIONS"]
