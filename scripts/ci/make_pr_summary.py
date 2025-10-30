#!/usr/bin/env python3
"""Generate a Markdown summary of CI artifacts for PR comments."""

from __future__ import annotations

import json
import sys
import tarfile
import xml.etree.ElementTree as ET
from contextlib import closing
from pathlib import Path

STATUS_ICONS: dict[str, str] = {
    "success": "✅",
    "completed": "✅",
    "neutral": "✅",
    "failure": "❌",
    "cancelled": "⚪",
    "timed_out": "⏱",
    "skipped": "⚪",
    "in_progress": "⏳",
    "queued": "⏳",
}


def parse_coverage_xml(path: Path) -> float | None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    line_rate = root.attrib.get("line-rate")
    if not line_rate:
        return None
    try:
        return float(line_rate) * 100
    except ValueError:
        return None


def parse_coverage_txt(path: Path) -> float | None:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        text = line.strip()
        if not text:
            continue
        if text.startswith("TOTAL") or text.endswith("%"):
            tokens = text.replace("%", " ").split()
            for token in reversed(tokens):
                try:
                    return float(token)
                except ValueError:
                    continue
    return None


def gather_coverage(root: Path) -> tuple[dict[str, float], dict[str, set[str]]]:
    coverage: dict[str, float] = {}
    artifacts: dict[str, set[str]] = {}
    for xml_path in root.rglob("coverage-*.xml"):
        service = xml_path.stem.replace("coverage-", "")
        value = parse_coverage_xml(xml_path)
        if value is not None:
            coverage[service] = value
        artifacts.setdefault(service, set()).add(xml_path.name)
    for txt_path in root.rglob("coverage-*.txt"):
        service = txt_path.stem.replace("coverage-", "")
        if service not in coverage:
            value = parse_coverage_txt(txt_path)
            if value is not None:
                coverage[service] = value
        artifacts.setdefault(service, set()).add(txt_path.name)
    return coverage, artifacts


def bundle_failed(bundle: Path) -> bool:
    try:
        with tarfile.open(bundle, mode="r:*") as archive:
            for member in archive.getmembers():
                if not member.isfile() or member.size == 0:
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    continue
                with closing(extracted) as fh:
                    try:
                        content = fh.read().decode("utf-8", errors="ignore")
                    except Exception:
                        continue
                    if "Process completed with exit code 1" in content:
                        return True
    except (tarfile.TarError, OSError):
        return False
    return False


def infer_status_from_bundle(root: Path, service: str) -> str:
    patterns = [
        f"debug-bundle-{service}.tar.gz",
        f"debug-bundle-{service}.tgz",
    ]
    for pattern in patterns:
        for bundle in root.rglob(pattern):
            return "❌" if bundle_failed(bundle) else "✅"
    return "✅"


def load_jobs(root: Path) -> dict[str, tuple[str | None, str | None]]:
    jobs_file = root / "jobs.json"
    if not jobs_file.exists():
        return {}
    try:
        data = json.loads(jobs_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    mapping: dict[str, tuple[str | None, str | None]] = {}
    for entry in data:
        name = entry.get("name")
        if not name:
            continue
        url = entry.get("url")
        status = entry.get("status")
        mapping[name] = (url, status)
    return mapping


def status_icon(status: str | None) -> str | None:
    if not status:
        return None
    lowered = status.lower()
    return STATUS_ICONS.get(lowered, None)


def index_artifacts(root: Path) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    if not root.exists():
        return index
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        files = sorted(
            p.relative_to(child).as_posix() for p in child.rglob("*") if p.is_file()
        )
        index[child.name] = files
    return index


def artifacts_for_service(service: str, index: dict[str, list[str]]) -> list[str]:
    keys = [
        f"coverage-{service}",
        f"logs-{service}",
        f"debug-bundle-{service}",
    ]
    collected: list[str] = []
    for key in keys:
        files = index.get(key)
        if not files:
            continue
        if len(files) == 1:
            collected.append(f"{key}/{files[0]}")
        else:
            collected.extend(f"{key}/{file}" for file in files)
    return collected


def resolve_status(
    root: Path,
    job_map: dict[str, tuple[str | None, str | None]],
    job_name: str,
    service: str,
) -> str:
    job = job_map.get(job_name)
    icon = status_icon(job[1]) if job else None
    if icon:
        return icon
    return infer_status_from_bundle(root, service)


def resolve_log_link(
    job_map: dict[str, tuple[str | None, str | None]], job_name: str
) -> str:
    job = job_map.get(job_name)
    url = job[0] if job else None
    return f"[Log]({url})" if url else "N/A"


def format_percentage(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}%"


def build_table(
    services: list[str],
    coverage: dict[str, float],
    coverage_artifacts: dict[str, set[str]],
    artifact_index: dict[str, list[str]],
    job_map: dict[str, tuple[str | None, str | None]],
    root: Path,
) -> str:
    if not services:
        return "No artifacts found."

    header = "| Service | Status | Coverage | Artifacts | Logs |"
    separator = "|---|:---:|---:|---|---|"
    lines = [header, separator]

    for service in services:
        if service in ("lint", "migrations"):
            job_name = service
            coverage_value = None
        else:
            job_name = f"pytest ({service})"
            coverage_value = coverage.get(service)

        status = resolve_status(root, job_map, job_name, service)
        logs = resolve_log_link(job_map, job_name)

        coverage_entries = {
            f"coverage-{service}/{name}"
            for name in coverage_artifacts.get(service, set())
        }
        artifact_entries = coverage_entries.union(
            set(artifacts_for_service(service, artifact_index))
        )
        artifacts_display = (
            ", ".join(sorted(artifact_entries)) if artifact_entries else "N/A"
        )

        lines.append(
            "| "
            f"{service} | {status} | {format_percentage(coverage_value)} | "
            f"{artifacts_display} | {logs} |"
        )

    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: make_pr_summary.py <artifacts_dir>", file=sys.stderr)
        return 1

    root = Path(sys.argv[1]).resolve()
    if not root.exists():
        print(f"Artifacts directory not found: {root}", file=sys.stderr)
        return 1

    coverage, coverage_artifacts = gather_coverage(root)
    job_map = load_jobs(root)
    artifact_index = index_artifacts(root)

    service_names: set[str] = {name for name in coverage.keys() if name != "aggregate"}
    for job_name in job_map:
        if job_name.startswith("pytest (") and job_name.endswith(")"):
            service_names.add(job_name[len("pytest (") : -1])
    service_names.update({"lint", "migrations"})

    ordered_services = sorted(
        name for name in service_names if name not in {"lint", "migrations"}
    )
    for tail in ("lint", "migrations"):
        if tail in service_names:
            ordered_services.append(tail)

    table = build_table(
        ordered_services,
        coverage,
        coverage_artifacts,
        artifact_index,
        job_map,
        root,
    )
    print(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
