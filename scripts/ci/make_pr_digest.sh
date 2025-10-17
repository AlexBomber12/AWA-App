#!/usr/bin/env bash
set -euo pipefail

LOG_ROOT="${1:-.}"
TAIL_N="${TAIL_N:-150}"
ERR_N="${ERR_N:-120}"
MIRROR_PATH="${MIRROR_PATH:-}"
PREVIEW_URL="${PREVIEW_URL:-}"
DIGEST_FILE="${DIGEST_FILE:-ci-digest.md}"
BODY_LIMIT="${BODY_LIMIT:-65000}"

if git rev-parse --short HEAD >/dev/null 2>&1; then
  SHORT_SHA="$(git rev-parse --short HEAD)"
else
  SHORT_SHA="${GITHUB_SHA:-unknown}"
  SHORT_SHA="${SHORT_SHA:0:8}"
fi

export LOG_ROOT TAIL_N ERR_N MIRROR_PATH PREVIEW_URL DIGEST_FILE BODY_LIMIT SHORT_SHA

python - <<'PY'
import math
import os
import pathlib
import re
from typing import List

log_root = pathlib.Path(os.environ.get("LOG_ROOT", ".")).resolve()
tail_n = int(os.environ.get("TAIL_N", "150"))
err_n = int(os.environ.get("ERR_N", "120"))
mirror_path = os.environ.get("MIRROR_PATH", "").strip() or "n/a"
preview_url = os.environ.get("PREVIEW_URL", "").strip() or "n/a"
digest_file = os.environ.get("DIGEST_FILE", "ci-digest.md")
body_limit = int(os.environ.get("BODY_LIMIT", "65000"))
short_sha = os.environ.get("SHORT_SHA", "unknown")
digest_path = pathlib.Path(digest_file)
if not digest_path.is_absolute():
    digest_path = log_root / digest_path

log_targets = [
    ("integ.log", "Integration tests"),
    ("unit.log", "Unit tests"),
    ("compose-logs.txt", "docker compose logs"),
    ("docker-build.log", "Docker build"),
    ("vitest.log", "Vitest"),
    ("tsc.log", "TypeScript"),
    ("eslint.log", "ESLint"),
]

errors_pattern = re.compile(r"(ERROR|FATAL|Traceback|E\s+\d+|^\s*at\s+)", re.IGNORECASE | re.MULTILINE)
key_pattern = re.compile(r"([A-Za-z0-9_]*?(?:TOKEN|SECRET|PASSWORD|API_KEY|DSN|AUTH|COOKIE)[A-Za-z0-9_]*=)([^\s]+)", re.IGNORECASE)
url_pattern = re.compile(r"(://[^:@\s/]+:)([^@\s]+)(@)")

def sanitize_text(value: str) -> str:
    text = value
    for _ in range(2):
        text = key_pattern.sub(lambda m: m.group(1) + '<redacted>', text)
        text = url_pattern.sub(lambda m: m.group(1) + '****' + m.group(3), text)
    return text

def read_text(path: pathlib.Path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None

error_entries = []
remaining = err_n
for filename, label in log_targets:
    if remaining <= 0:
        break
    content = read_text(log_root / filename)
    if not content:
        continue
    lines = content.splitlines()
    matches = [line for line in lines if errors_pattern.search(line)]
    if not matches:
        continue
    snippet = matches[:remaining]
    remaining -= len(snippet)
    error_entries.append((label, filename, snippet))

TailEntry = dict

def collect_tails() -> List[TailEntry]:
    entries: List[TailEntry] = []
    for filename, label in log_targets:
        content = read_text(log_root / filename)
        if not content:
            continue
        lines = content.splitlines()
        if not lines:
            continue
        limited = lines[-tail_n:]
        entries.append({"label": label, "filename": filename, "lines": limited})
    return entries

tail_entries = collect_tails()

header_lines = [
    "<!-- AWA-CI-DIGEST -->",
    f"## CI digest for `{short_sha}`",
    "",
    f"- **Preview**: {preview_url}",
    f"- **Mirror path**: {mirror_path}",
    "- **Artifacts**: Download debug bundles from the workflow run.",
]

if error_entries:
    error_section: List[str] = ["", "### First errors", ""]
    for label, filename, snippet in error_entries:
        error_section.append(f"**{label}** (`{filename}`)")
        error_section.append("")
        error_section.append("```")
        error_section.extend(snippet)
        error_section.append("```")
        error_section.append("")
else:
    error_section = ["", "### First errors", "", "_No matching error patterns found in the inspected logs._", ""]


def build_tails(scale: float) -> List[str]:
    if not tail_entries:
        return ["", "### Log tails", "", "_No log files were found for tail rendering._", ""]
    lines: List[str] = ["", "### Log tails", ""]
    for entry in tail_entries:
        source_lines = entry["lines"]
        if not source_lines:
            continue
        count = int(math.ceil(len(source_lines) * scale)) if scale > 0 else 0
        count = max(0, min(len(source_lines), count))
        if count == 0 and scale > 0:
            count = 1
        if count == 0:
            summary = f"{entry['label']} (`{entry['filename']}`) — tail omitted"
            lines.append("<details>")
            lines.append(f"<summary>{summary}</summary>")
            lines.append("")
            lines.append("_Tail omitted to meet size constraints._")
            lines.append("")
            lines.append("</details>")
            lines.append("")
            continue
        selected = source_lines[-count:]
        summary = f"{entry['label']} (`{entry['filename']}`) — last {len(selected)} lines"
        lines.append("<details>")
        lines.append(f"<summary>{summary}</summary>")
        lines.append("")
        lines.append("```")
        lines.extend(selected)
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    return lines


def render(scale: float) -> str:
    lines = header_lines + error_section + build_tails(scale)
    body = "\n".join(lines).strip() + "\n"
    return sanitize_text(body)

full_text = render(1.0)
if len(full_text) > body_limit:
    lo, hi = 0.0, 1.0
    best = None
    for _ in range(25):
        mid = (lo + hi) / 2
        candidate = render(mid)
        if len(candidate) <= body_limit:
            best = candidate
            lo = mid
        else:
            hi = mid
    if best is not None:
        full_text = best
    else:
        minimal = render(0.0)
        if len(minimal) > body_limit:
            full_text = minimal[:body_limit]
        else:
            full_text = minimal

digest_path.write_text(full_text, encoding="utf-8")
PY
