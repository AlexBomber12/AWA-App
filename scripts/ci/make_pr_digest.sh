#!/usr/bin/env bash
set -euo pipefail

TAIL_N=${TAIL_N:-150}
ERR_N=${ERR_N:-120}
MIRROR_PATH=${MIRROR_PATH:-}
LOG_DIR=${1:-digest_logs}
DIGEST=ci-digest.md

sanitize() {
  sed -E 's/(TOKEN|SECRET|PASSWORD|API_KEY|DSN|AUTH|COOKIE)[^[:space:]]*/[REDACTED]/Ig' | \
  sed -E 's#://([^:/\n]+):([^@/\n]+)@#://\1:****@#g'
}

first_errors() {
  local out=""
  declare -A files=(
    [integ.log]="integration pytest",
    [compose-logs.txt]="compose logs",
    [unit.log]="unit pytest",
    [vitest.log]="frontend",
    [docker-build.log]="docker build"
  )
  for f in integ.log compose-logs.txt unit.log vitest.log docker-build.log; do
    [ -f "$LOG_DIR/$f" ] || continue
    line=$(grep -m1 -E 'ERROR|FATAL|Traceback' "$LOG_DIR/$f" || true)
    [ -n "$line" ] && out+="${files[$f]}: $line\n"
  done
  echo -n "$out" | head -n "$ERR_N"
}

tail_block() {
  local file="$1" label="$2"
  [ -f "$LOG_DIR/$file" ] || return 0
  echo "<details><summary>$label tail</summary>" >> "$DIGEST.tmp"
  echo >> "$DIGEST.tmp"
  echo '```' >> "$DIGEST.tmp"
  tail -n "$TAIL_N" "$LOG_DIR/$file" >> "$DIGEST.tmp"
  echo '```' >> "$DIGEST.tmp"
  echo >> "$DIGEST.tmp"
  echo '</details>' >> "$DIGEST.tmp"
  echo >> "$DIGEST.tmp"
}

generate() {
  local preview="n/a"
  [ -f "$LOG_DIR/preview-url.txt" ] && preview=$(cat "$LOG_DIR/preview-url.txt")
  local errors
  errors=$(first_errors)
  {
    echo '<!-- CI_LOG_MIRROR -->'
    echo '# CI last run logs (sanitized)'
    echo
    echo "Preview URL: ${preview}"
    echo
    echo "Artifacts: download debug-bundle in Artifacts${MIRROR_PATH:+ (mirrored at $MIRROR_PATH)}"
    echo
    echo '## First errors'
    echo '```'
    echo "$errors"
    echo '```'
    echo
  } > "$DIGEST.tmp"
  tail_block unit.log "unit.log"
  tail_block integ.log "integ.log"
  tail_block vitest.log "vitest.log"
  tail_block tsc.log "tsc.log"
  tail_block eslint.log "eslint.log"
  tail_block compose-logs.txt "compose-logs.txt"
  tail_block docker-build.log "docker-build.log"
}

while true; do
  generate
  sanitize < "$DIGEST.tmp" | sanitize > "$DIGEST"
  size=$(wc -c < "$DIGEST")
  if [ "$size" -le 60000 ] || [ "$TAIL_N" -le 10 ]; then
    break
  fi
  TAIL_N=$((TAIL_N/2))
  echo "Digest too large ($size chars), reducing tail to $TAIL_N" >&2

done

rm -f "$DIGEST.tmp"
