#!/usr/bin/env python3
"""
Enforce per-package coverage thresholds for critical backend modules.

Usage: python scripts/ci/check_coverage_thresholds.py coverage.xml
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Threshold:
    line: float
    branch: float


THRESHOLDS: dict[str, Threshold] = {
    "api.routes": Threshold(line=80.0, branch=60.0),
    "worker": Threshold(line=75.0, branch=55.0),
    "etl": Threshold(line=65.0, branch=35.0),
    "awa_common.etl": Threshold(line=85.0, branch=70.0),
}


def load_package_metrics(path: Path) -> dict[str, Threshold]:
    tree = ET.parse(path)
    packages: dict[str, Threshold] = {}
    for pkg in tree.findall(".//package"):
        name = pkg.get("name")
        if not name:
            continue
        line_rate = float(pkg.get("line-rate", 0.0)) * 100
        branch_rate = float(pkg.get("branch-rate", 0.0)) * 100
        packages[name] = Threshold(line=line_rate, branch=branch_rate)
    return packages


def evaluate(packages: dict[str, Threshold], required: dict[str, Threshold]) -> Iterable[str]:
    for name, threshold in required.items():
        if name not in packages:
            yield f"Missing coverage entry for '{name}' in coverage.xml"
            continue
        metrics = packages[name]
        if metrics.line < threshold.line:
            yield f"{name}: line coverage {metrics.line:.1f}% below {threshold.line:.1f}%"
        if metrics.branch < threshold.branch:
            yield f"{name}: branch coverage {metrics.branch:.1f}% below {threshold.branch:.1f}%"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/ci/check_coverage_thresholds.py coverage.xml", file=sys.stderr)
        return 2

    coverage_path = Path(sys.argv[1])
    if not coverage_path.exists():
        print(f"Coverage file not found: {coverage_path}", file=sys.stderr)
        return 1

    packages = load_package_metrics(coverage_path)
    failures = list(evaluate(packages, THRESHOLDS))
    if failures:
        print("Coverage thresholds failed:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("Coverage thresholds satisfied for critical modules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
