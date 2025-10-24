#!/usr/bin/env bash
set -Eeuo pipefail
mapfile -t paths < <(git ls-files -z \
  | tr '\0' '\n' \
  | grep -E '(^|/)(\.local-artifacts|artifacts|__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|coverage(\.xml)?|htmlcov|dist|build|node_modules|webapp/\.next|webapp/(out|build)|\.codex)($|/)' \
  || true)
if [ "${#paths[@]}" -gt 0 ]; then
  git rm -r --cached -- "${paths[@]}"
fi
