#!/usr/bin/env python3
"""Generate a Markdown summary of CI artifacts for PR comments."""

from __future__ import annotations

import json
import re
import sys
import tarfile
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


def coverage_service_name(stem: str) -> str:
    if stem.startswith("coverage-"):
        stem = stem[len("coverage-") :]
    if stem == "aggregate":
        return "coverage-aggregate"
    return stem


def parse_coverage_xml(path: Path) -> float | None:
    import xml.etree.ElementTree as ET

    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
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
            match = re.search(r"(\d+(?:\.\d+)?)%", text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
    return None


def gather_coverage(root: Path) -> tuple[dict[str, float], dict[str, set[str]]]:
    coverage: dict[str, float] = {}
    coverage_artifacts: dict[str, set[str]] = {}
    for xml_path in root.rglob("coverage-*.xml"):
        service = coverage_service_name(xml_path.stem)
        value = parse_coverage_xml(xml_path)
        if value is not None:
            coverage[service] = value
        coverage_artifacts.setdefault(service, set()).add(
            xml_path.relative_to(root).as_posix()
        )
    for txt_path in root.rglob("coverage-*.txt"):
        service = coverage_service_name(txt_path.stem)
        if service not in coverage:
            value = parse_coverage_txt(txt_path)
            if value is not None:
                coverage[service] = value
        coverage_artifacts.setdefault(service, set()).add(
            txt_path.relative_to(root).as_posix()
        )
    return coverage, coverage_artifacts


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
    return STATUS_ICONS.get(status.lower())


def job_name_for_service(service: str) -> str:
    if service == "coverage-aggregate":
        return "coverage aggregate"
    if service in {"lint", "migrations"}:
        return service
    return f"pytest ({service})"


def resolve_status(
    root: Path, job_map: dict[str, tuple[str | None, str | None]], service: str
) -> str:
    job_name = job_name_for_service(service)
    job = job_map.get(job_name)
    icon = status_icon(job[1]) if job else None
    if icon:
        return icon
    return infer_status_from_bundle(root, service)


def resolve_log_link(
    job_map: dict[str, tuple[str | None, str | None]], service: str
) -> str:
    job_name = job_name_for_service(service)
    job = job_map.get(job_name)
    url = job[0] if job else None
    return f"[Log]({url})" if url else "N/A"


def index_artifacts(root: Path) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    if not root.exists():
        return index
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        files = sorted(
            path.relative_to(child).as_posix()
            for path in child.rglob("*")
            if path.is_file()
        )
        index[child.name] = files
    return index


def artifacts_for_service(service: str, index: dict[str, list[str]]) -> list[str]:
    keys = {f"logs-{service}", f"debug-bundle-{service}"}
    if service == "coverage-aggregate":
        keys.add("coverage-aggregate")
    else:
        keys.add(f"coverage-{service}")
    entries: set[str] = set()
    for key in keys:
        files = index.get(key)
        if not files:
            continue
        entries.update(f"{key}/{name}" for name in files)
    return sorted(entries)


def format_percentage(value: float | None) -> str:
    return f"{value:.2f}%" if value is not None else "N/A"


def read_overall_coverage(root: Path) -> float | None:
    for path in root.rglob("coverage-aggregate.txt"):
        value = parse_coverage_txt(path)
        if value is not None:
            return value
    return None


def read_diff_coverage(root: Path) -> tuple[float | None, str | None, bool | None]:
    diff_path = next(root.rglob("diff-coverage.txt"), None)
    base_path = next(root.rglob("diff-base.txt"), None)
    base = None
    if base_path and base_path.exists():
        base = base_path.read_text(encoding="utf-8", errors="ignore").strip() or None
    if not diff_path or not diff_path.exists():
        return None, base, None
    text = diff_path.read_text(encoding="utf-8", errors="ignore")
    matches = re.findall(r"(\d+(?:\.\d+)?)%", text)
    value = float(matches[-1]) if matches else None
    passed = None if value is None else value >= 70.0 - 1e-9
    return value, base, passed


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
        coverage_value = (
            coverage.get(service) if service not in {"lint", "migrations"} else None
        )
        status = resolve_status(root, job_map, service)
        logs = resolve_log_link(job_map, service)

        coverage_entries = coverage_artifacts.get(service, set())
        artifact_entries = set(coverage_entries)
        artifact_entries.update(artifacts_for_service(service, artifact_index))
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

    service_names: set[str] = set(coverage.keys())
    for job_name in job_map:
        if job_name.startswith("pytest (") and job_name.endswith(")"):
            service_names.add(job_name[len("pytest (") : -1])
        elif job_name in {"lint", "migrations", "coverage aggregate"}:
            if job_name == "coverage aggregate":
                service_names.add("coverage-aggregate")
            else:
                service_names.add(job_name)

    service_names.update({"lint", "migrations"})
    if "coverage-aggregate" in coverage or "coverage aggregate" in job_map:
        service_names.add("coverage-aggregate")

    ordered_services = sorted(
        name
        for name in service_names
        if name not in {"coverage-aggregate", "lint", "migrations"}
    )
    if "coverage-aggregate" in service_names:
        ordered_services.append("coverage-aggregate")
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

    lines: list[str] = []

    overall = read_overall_coverage(root)
    if overall is not None:
        lines.append(f"Overall coverage (info): {overall:.2f}%")

    diff_value, diff_base, diff_pass = read_diff_coverage(root)
    if diff_value is not None:
        base_label = diff_base or "base"
        if diff_pass is None:
            lines.append(
                f"Diff coverage vs {base_label}: {diff_value:.2f}% (target 70%)"
            )
        else:
            icon = "✅" if diff_pass else "❌"
            lines.append(
                f"Diff coverage vs {base_label}: {icon} {diff_value:.2f}% (target 70%)"
            )

    if lines:
        lines.append("")
    lines.append(table)

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
