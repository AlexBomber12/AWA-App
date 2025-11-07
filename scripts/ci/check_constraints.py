#!/usr/bin/env python3
"""Verify single constraints policy for CI."""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONSTRAINT = ROOT / "constraints.txt"
violations: list[str] = []

other_constraints = sorted(
    path for path in ROOT.glob("**/constraints*.txt") if path != CONSTRAINT and not path.is_symlink()
)
if other_constraints:
    formatted = "\n".join(str(path.relative_to(ROOT)) for path in other_constraints)
    violations.append("Found unexpected constraint file(s):\n" + formatted)

for req_path in sorted(
    list(ROOT.glob("services/**/requirements.txt")) + list(ROOT.glob("packages/**/requirements.txt"))
):
    for idx, line in enumerate(req_path.read_text().splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("-"):
            # Allow includes such as -c or extra pip flags
            continue
        without_comment = stripped.split("#", 1)[0].strip()
        requirement_part = without_comment.split(";", 1)[0].strip()
        if "==" in requirement_part:
            rel = req_path.relative_to(ROOT)
            violations.append(f"{rel}:{idx}: contains version pin '{requirement_part}'")

if violations:
    print("Constraints policy violations detected:\n", file=sys.stderr)
    for message in violations:
        print(f"- {message}", file=sys.stderr)
    sys.exit(1)

sys.exit(0)
