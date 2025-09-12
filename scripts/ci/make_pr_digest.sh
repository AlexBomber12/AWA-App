#!/usr/bin/env bash
set -Eeuo pipefail
TAIL_N="${TAIL_N:-150}"         # lines per tail section
ERR_N="${ERR_N:-80}"            # lines of first matching errors
OUT="ci-digest.md"

sanitize() {
  sed -E 's/(TOKEN|SECRET|PASSWORD|KEY|DSN|AUTH|COOKIE)=\S+/\1=REDACTED/g' \
  | sed -E 's#([a-z]+://[^:/]+):[^@]+@#\1:****@#g'
}

section() {
  local title="$1"; shift
  echo "<details><summary><strong>${title}</strong></summary>"
  echo
  echo '```txt'
  cat | sanitize
  echo '```'
  echo
  echo '</details>'
  echo
}

first_errors() {
  # print first ERR_N lines around the first occurrences
  local f="$1"
  if [ -f "$f" ]; then
    awk 'BEGIN{IGNORECASE=1} /ERROR|FATAL|Traceback/{print NR ":" $0; c++} c>0 && c<10{print; c++}' "$f" \
      | head -n "$ERR_N"
  fi
}

preview_url="$(test -f preview-url.txt && cat preview-url.txt || echo "n/a")"
mirror_path="${MIRROR_PATH:-n/a}"   # set by caller

{
  echo "<!-- AWA-CI-DIGEST v2 -->"
  echo "### CI Digest"
  echo "- Commit: \`$(git rev-parse --short HEAD 2>/dev/null || echo unknown)\`"
  echo "- Preview: ${preview_url}"
  echo "- Mirror logs: \`${mirror_path}\`"
  echo "- Artifacts: download **debug-bundle** from the run’s Artifacts panel"
  echo

  # Errors (compact)
  echo "#### First errors (compact)"
  echo '```txt'
  for f in unit.log integ.log vitest.log tsc.log eslint.log compose-integration-logs.txt docker-build.log; do
    if [ -f "$f" ]; then
      echo "--- ${f} ---"
      first_errors "$f" | sanitize
    fi
  done
  echo '```'
  echo

  # Tails (collapsible)
  for f in unit.log integ.log vitest.log tsc.log eslint.log compose-integration-logs.txt; do
    if [ -f "$f" ]; then
      echo
      section "Tail: $f (last ${TAIL_N} lines)" < <(tail -n "$TAIL_N" "$f")
    fi
  done
} > "$OUT"
echo "Wrote $OUT"
