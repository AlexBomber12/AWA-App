#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 [--repo owner/name] [--run-id RUN_ID] [--dir DIR]

Download the latest (or specified) mirrorlogs artifact from GitHub Actions
using the GitHub CLI. Requires 'gh' to be installed and authenticated
(install via brew/apt and run 'gh auth login').
USAGE
}

REPO="${REPO:-}"
RUN_ID=""
OUT_DIR="${OUT_DIR:-./mirrorlogs_download}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="$2"
      shift 2
      ;;
    --run-id)
      RUN_ID="$2"
      shift 2
      ;;
    --dir)
      OUT_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "The GitHub CLI (gh) is required. Install via 'brew install gh' or 'apt install gh'." >&2
  exit 1
fi

if [[ -z "${REPO}" ]]; then
  REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)
fi

if [[ -z "${REPO}" ]]; then
  REPO=$(git config --get remote.origin.url | sed -E 's#.*github.com[:/](.+)\.git#\1#')
fi

if [[ -z "${REPO}" ]]; then
  echo "Unable to determine the GitHub repo. Pass --repo owner/name." >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"

if [[ -n "${RUN_ID}" ]]; then
  gh run download "${RUN_ID}" --repo "${REPO}" --name mirrorlogs --dir "${OUT_DIR}"
else
  gh run download --repo "${REPO}" --name mirrorlogs --dir "${OUT_DIR}"
fi

echo "Mirror logs downloaded to ${OUT_DIR}"
