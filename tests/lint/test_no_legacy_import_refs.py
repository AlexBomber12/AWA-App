from __future__ import annotations

import ast
import subprocess
from pathlib import Path

LEGACY_MODULES = ("legacy", "etl.legacy")


def _tracked_python_files() -> list[Path]:
    result = subprocess.run(["git", "ls-files", "*.py"], check=True, capture_output=True, text=True)
    files = []
    for line in result.stdout.splitlines():
        path = Path(line.strip())
        if not path or str(path).startswith("legacy/"):
            continue
        files.append(path)
    return files


def _has_legacy_import(content: str) -> bool:
    try:
        module = ast.parse(content)
    except SyntaxError:
        return False
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_legacy_name(alias.name):
                    return True
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            if _is_legacy_name(module_name):
                return True
            if module_name == "etl" and any(alias.name == "legacy" for alias in node.names):
                return True
    return False


def _is_legacy_name(name: str) -> bool:
    return any(name == mod or name.startswith(f"{mod}.") for mod in LEGACY_MODULES)


def test_no_legacy_imports() -> None:
    offenders = []
    for path in _tracked_python_files():
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if _has_legacy_import(content):
            offenders.append(path)
    assert not offenders, "Legacy imports found:\n" + "\n".join(str(p) for p in offenders)
