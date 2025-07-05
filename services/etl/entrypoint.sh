#!/usr/bin/env bash
set -euo pipefail

./wait_db.sh
python keepa_ingestor.py
