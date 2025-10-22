#!/usr/bin/env bash
set -euo pipefail
FILES=$(find services -maxdepth 2 -name 'requirements*.txt' -print | sort)
FILES="$FILES requirements-dev.txt"
pip-compile --no-annotate --no-header -o constraints.txt $FILES
