#!/usr/bin/env bash
set -euo pipefail

./wait-for-postgres.sh
python keepa_ingestor.py
