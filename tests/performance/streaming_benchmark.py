from __future__ import annotations

import argparse
import os
import resource
import tempfile
import time
from pathlib import Path

from etl import load_csv


def _write_synthetic_csv(path: Path, size_mb: int) -> int:
    header = "asin,qty,refund_amount,return_reason,return_date,currency\n"
    row_template = "ASIN{idx:09d},1,2.5,damaged,2024-01-01,USD\n"
    target_bytes = size_mb * 1024 * 1024
    bytes_written = 0
    with path.open("w", encoding="utf-8") as handle:
        handle.write(header)
        bytes_written += len(header.encode("utf-8"))
        idx = 0
        while bytes_written < target_bytes:
            row = row_template.format(idx=idx)
            handle.write(row)
            bytes_written += len(row.encode("utf-8"))
            idx += 1
    return bytes_written


def _rss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is kilobytes on Linux, bytes on macOS. Normalize via heuristics.
    raw = usage.ru_maxrss
    if raw > 10_000_000:  # assume bytes on macOS
        return raw / (1024 * 1024)
    return raw / 1024


def run_benchmark(size_mb: int, chunk_size: int, limit_mb: int) -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        csv_path = Path(tmp.name)
    try:
        actual_bytes = _write_synthetic_csv(csv_path, size_mb)
        start = time.perf_counter()
        before = _rss_mb()
        peak = before
        row_count = 0
        for chunk in load_csv.load_large_csv(csv_path, chunk_size=chunk_size):
            row_count += len(chunk)
            peak = max(peak, _rss_mb())
        duration = time.perf_counter() - start
        peak_delta = peak - before
        print(
            f"Processed {actual_bytes / 1024 / 1024:.1f} MB ({row_count} rows) "
            f"in {duration:.2f}s with +{peak_delta:.1f} MB RSS (chunk={chunk_size})."
        )
        if peak > limit_mb:
            raise SystemExit(
                f"Peak RSS {peak:.1f} MB exceeded limit of {limit_mb} MB. "
                "Reduce chunk size or investigate memory usage."
            )
    finally:
        try:
            os.remove(csv_path)
        except FileNotFoundError:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark streaming ingest memory usage.")
    parser.add_argument("--size-mb", type=int, default=120, help="Approximate CSV size to generate (default: 120 MB)")
    parser.add_argument("--chunk-size", type=int, default=50000, help="Rows per chunk to load (default: 50000)")
    parser.add_argument(
        "--max-memory-mb",
        type=int,
        default=350,
        help="Fail if peak RSS exceeds this many MB (default: 350)",
    )
    args = parser.parse_args()
    run_benchmark(args.size_mb, args.chunk_size, args.max_memory_mb)


if __name__ == "__main__":
    main()
