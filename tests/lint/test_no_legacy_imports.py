from __future__ import annotations

import re
import subprocess
from pathlib import Path

LEGACY_PATTERN = re.compile(r"^(?:from|import)\s+legacy(?:\.|\s|$)", re.MULTILINE)


def _tracked_python_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "*.py"], check=True, capture_output=True, text=True
    )
    files = []
    for line in result.stdout.splitlines():
        path = Path(line.strip())
        if not path or str(path).startswith("legacy/"):
            continue
        files.append(path)
    return files


def test_no_legacy_imports() -> None:
    offenders = []
    for path in _tracked_python_files():
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if LEGACY_PATTERN.search(content):
            offenders.append(path)
    assert not offenders, "Legacy imports found:\n" + "\n".join(
        str(p) for p in offenders
    )
