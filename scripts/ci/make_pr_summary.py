#!/usr/bin/env python3
"""Generate a Markdown summary of CI artifacts for PR comments."""

from __future__ import annotations

import sys
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path


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
        line = line.strip()
        if not line:
            continue
        if line.startswith("TOTAL") or line.endswith("%"):
            tokens = line.replace("%", " ").split()
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
                with archive.extractfile(member) as extracted:
                    if extracted is None:
                        continue
                    try:
                        content = extracted.read().decode("utf-8", errors="ignore")
                    except Exception:
                        continue
                    if "Process completed with exit code 1" in content:
                        return True
    except (tarfile.TarError, OSError):
        return False
    return False


def infer_status(root: Path, service: str) -> str:
    patterns = [
        f"debug-bundle-{service}.tar.gz",
        f"debug-bundle-{service}.tgz",
    ]
    if service == "aggregate":
        patterns.extend(
            [
                "debug-bundle-coverage-aggregate.tar.gz",
                "debug-bundle-coverage-aggregate.tgz",
            ]
        )
    for pattern in patterns:
        for bundle in root.rglob(pattern):
            return "❌" if bundle_failed(bundle) else "✅"
    return "✅"


def format_percentage(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}%"


def build_table(
    coverage: dict[str, float], artifacts: dict[str, set[str]], root: Path
) -> str:
    if not coverage:
        return "No coverage data available."
    services = sorted(coverage.keys(), key=lambda item: (item == "aggregate", item))
    headers = ["Service", "Tests Status", "Coverage", "Artifacts"]
    rows: list[list[str]] = [headers]
    for service in services:
        cov = coverage.get(service)
        status = infer_status(root, service)
        artifact_list = sorted(artifacts.get(service, set()))
        artifact_display = ", ".join(artifact_list) if artifact_list else "N/A"
        rows.append(
            [
                service,
                status,
                format_percentage(cov),
                artifact_display,
            ]
        )
    header_line = "| " + " | ".join(rows[0]) + " |"
    separator = "|---|---:|---:|---|"
    body_lines = [
        "| "
        + " | ".join(
            [
                row[0],
                row[1].rjust(len(row[1])),
                row[2].rjust(len(row[2])),
                row[3],
            ]
        )
        + " |"
        for row in rows[1:]
    ]
    return "\n".join([header_line, separator, *body_lines])


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: make_pr_summary.py <artifacts_dir>", file=sys.stderr)
        return 1
    root = Path(sys.argv[1]).resolve()
    if not root.exists():
        print(f"Artifacts directory not found: {root}", file=sys.stderr)
        return 1
    coverage, artifacts = gather_coverage(root)
    table = build_table(coverage, artifacts, root)
    print(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
