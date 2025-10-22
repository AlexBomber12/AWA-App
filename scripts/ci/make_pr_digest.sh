#!/usr/bin/env bash
set -euo pipefail

LOG_ROOT="${1:-.}"
MIRROR_PATH="${MIRROR_PATH:-}"
PREVIEW_URL="${PREVIEW_URL:-}"
DIGEST_FILE="${DIGEST_FILE:-ci-digest.md}"
BODY_LIMIT="${BODY_LIMIT:-65000}"
FAILED_TAIL_LINES="${FAILED_TAIL_LINES:-200}"

if git rev-parse --short HEAD >/dev/null 2>&1; then
  SHORT_SHA="$(git rev-parse --short HEAD)"
else
  SHORT_SHA="${GITHUB_SHA:-unknown}"
  SHORT_SHA="${SHORT_SHA:0:8}"
fi

export LOG_ROOT MIRROR_PATH PREVIEW_URL DIGEST_FILE BODY_LIMIT FAILED_TAIL_LINES SHORT_SHA

python - <<'PY'
import json
import os
import pathlib
import re
import urllib.request

log_root = pathlib.Path(os.environ.get("LOG_ROOT", ".")).resolve()
mirror_path = os.environ.get("MIRROR_PATH", "").strip() or "n/a"
preview_url = os.environ.get("PREVIEW_URL", "").strip() or "n/a"
digest_file = os.environ.get("DIGEST_FILE", "ci-digest.md")
body_limit = int(os.environ.get("BODY_LIMIT", "65000"))
failed_tail_lines = int(os.environ.get("FAILED_TAIL_LINES", "200"))
short_sha = os.environ.get("SHORT_SHA", "unknown")
server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
repository = os.environ.get("GITHUB_REPOSITORY", "")
run_id = os.environ.get("GITHUB_RUN_ID", "")
token = os.environ.get("GITHUB_TOKEN", "")
run_url = (
    f"{server_url}/{repository}/actions/runs/{run_id}"
    if repository and run_id
    else server_url
)

digest_path = pathlib.Path(digest_file)
if not digest_path.is_absolute():
    digest_path = log_root / digest_path

def fetch_jobs():
    if not token or not repository or not run_id:
        return []
    jobs = []
    url = f"https://api.github.com/repos/{repository}/actions/runs/{run_id}/jobs?per_page=100"
    while url:
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
            link_header = response.headers.get("Link") or ""
        jobs.extend(payload.get("jobs", []))
        next_url = None
        for part in link_header.split(","):
            part = part.strip()
            if part.endswith('rel="next"') and part.startswith("<"):
                next_url = part[1 : part.find(">")]
                break
        url = next_url
    jobs.sort(key=lambda item: item.get("started_at") or "")
    return jobs

jobs = fetch_jobs()
job_rows = []
for job in jobs:
    conclusion = (job.get("conclusion") or job.get("status") or "").lower()
    display_conclusion = job.get("conclusion") or job.get("status") or "unknown"
    job_rows.append(
        {
            "name": job.get("name", "job"),
            "conclusion": conclusion,
            "display": display_conclusion.replace("_", " ").title(),
            "html_url": job.get("html_url") or run_url,
        }
    )

known_jobs = {row["name"] for row in job_rows}
if "preview" not in known_jobs and preview_url.lower() != "n/a":
    job_rows.append(
        {
            "name": "preview",
            "conclusion": "success",
            "display": "Success",
            "html_url": run_url,
        }
    )
    known_jobs.add("preview")

if not job_rows:
    job_rows = [
        {"name": "workflow", "conclusion": "unknown", "display": "Unknown", "html_url": run_url}
    ]
    known_jobs = {"workflow"}

status_emoji = {
    "success": "✅",
    "failure": "❌",
    "cancelled": "⚠️",
    "timed_out": "⚠️",
    "action_required": "⚠️",
    "in_progress": "⏳",
    "queued": "⏳",
    "neutral": "⚠️",
}

def render_conclusion(row):
    symbol = status_emoji.get(row["conclusion"], "⚪")
    return f"{symbol} {row['display']}"

header_lines = [
    "<!-- AWA-CI-DIGEST -->",
    f"## CI digest for `{short_sha}`",
    "",
    f"- **Preview URL**: {preview_url}",
    f"- **Mirror path**: {mirror_path}",
    f"- **Workflow run**: [{run_id or 'n/a'}]({run_url})",
    "",
    "| Job | Conclusion | URL |",
    "| --- | ---------- | --- |",
]
for row in job_rows:
    header_lines.append(
        f"| {row['name']} | {render_conclusion(row)} | [Logs]({row['html_url']}) |"
    )

log_suffixes = {".log", ".txt", ".out", ".err", ".json", ".xml", ".junit", ".tap"}
log_entries = []
if log_root.exists():
    for path in sorted(log_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in log_suffixes:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = path.relative_to(log_root)
        log_entries.append({
            "path": rel,
            "lines": content.splitlines(),
        })

job_lookup = {row["name"] for row in job_rows}

def job_from_filename(filename: pathlib.PurePath) -> str | None:
    stem = filename.name.split(".")[0]
    prefix = stem.split("-", 1)[0].lower()
    if prefix in job_lookup:
        return prefix
    return None

logs_by_job: dict[str, list[tuple[pathlib.PurePath, list[str]]]] = {}
for entry in log_entries:
    job_name = job_from_filename(entry["path"])
    if not job_name:
        continue
    logs_by_job.setdefault(job_name, []).append((entry["path"], entry["lines"]))

failure_states = {"failure", "cancelled", "timed_out", "action_required"}
failing_rows = [row for row in job_rows if row["conclusion"] in failure_states]

failed_section = ["", "### Failed tails", ""]
if failing_rows:
    for row in failing_rows:
        job_name = row["name"]
        job_logs = logs_by_job.get(job_name, [])
        if not job_logs:
            failed_section.append(f"_{job_name} has no captured logs._")
            failed_section.append("")
            continue
        for log_path, lines in job_logs:
            failed_section.append(f"**{job_name}** (`{log_path}`)")
            failed_section.append("")
            failed_section.append("```")
            failed_section.extend(lines[-failed_tail_lines:])
            failed_section.append("```")
            failed_section.append("")
else:
    failed_section.append("_All monitored jobs succeeded._")
    failed_section.append("")

key_pattern = re.compile(r"([A-Za-z0-9_]*?(?:TOKEN|SECRET|PASSWORD|API_KEY|DSN|AUTH|COOKIE)[A-Za-z0-9_]*=)([^\s]+)", re.IGNORECASE)
url_pattern = re.compile(r"(://[^:@\s/]+:)([^@\s]+)(@)")

def sanitize_text(value: str) -> str:
    text = value
    for _ in range(2):
        text = key_pattern.sub(lambda m: m.group(1) + '<redacted>', text)
        text = url_pattern.sub(lambda m: m.group(1) + '****' + m.group(3), text)
    return text

full_text = "\n".join(header_lines + failed_section).strip() + "\n"
full_text = sanitize_text(full_text)

if len(full_text) > body_limit:
    note = "\n\n_Truncated digest: original length exceeded limit._\n"
    allowed = max(0, body_limit - len(note))
    full_text = full_text[:allowed].rstrip() + note

digest_path.parent.mkdir(parents=True, exist_ok=True)
digest_path.write_text(full_text, encoding="utf-8")
latest_path = pathlib.Path('.codex/mirror-logs/latest.md')
latest_path.parent.mkdir(parents=True, exist_ok=True)
latest_path.write_text(full_text, encoding="utf-8")
PY
