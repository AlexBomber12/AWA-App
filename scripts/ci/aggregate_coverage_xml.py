#!/usr/bin/env python3
"""Aggregate coverage from XML reports as a fallback."""

from __future__ import annotations

import glob
import os
import xml.etree.ElementTree as ET


def main() -> int:
    threshold = float(os.environ.get("COV_FAIL_UNDER", "70"))
    xml_paths = glob.glob("coverage-artifacts/**/coverage-*.xml", recursive=True)

    total_lines = 0
    total_covered = 0

    for xml_path in xml_paths:
        try:
            root = ET.parse(xml_path).getroot()
        except (ET.ParseError, OSError):
            continue
        for line in root.findall(".//line"):
            total_lines += 1
            hits = int(line.get("hits", "0"))
            if hits > 0:
                total_covered += 1

    if total_lines == 0:
        print("No XML coverage files found")
        return 1

    percentage = 100.0 * total_covered / total_lines
    print(f"Aggregate coverage: {percentage:.2f}% (covered {total_covered} / {total_lines})")

    if percentage + 1e-9 < threshold:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
