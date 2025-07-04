#!/usr/bin/env bash
./wait-for-it.sh postgres:5432 --timeout=30 -- \
  python keepa_ingestor.py
