import os
import pathlib
import re
import shutil
import subprocess
import time

import pytest


def _run_with_retries(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command with exponential backoff retries."""
    result: subprocess.CompletedProcess[str] = subprocess.CompletedProcess(cmd, 1)
    for attempt in range(5):
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if result.returncode == 0:
            break
        time.sleep(2**attempt)
    return result


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_build_all_service_images(tmp_path: pathlib.Path) -> None:
    for df in pathlib.Path("services").glob("*/Dockerfile"):
        service_dir = df.parent
        if service_dir.name == "llm_server" and not os.getenv("CUDA_VISIBLE_DEVICES"):
            continue
        log_file = tmp_path / f"{service_dir.name}.log"

        # pre-pull all base images with retries
        for line in df.read_text().splitlines():
            match = re.match(r"FROM\s+(\S+)", line)
            if match:
                _run_with_retries(["docker", "pull", match.group(1)])

        result = _run_with_retries(["docker", "build", str(service_dir), "-t", "awa-tmp"])
        log_file.write_text(result.stdout)
        if result.returncode != 0:
            pytest.fail(f"docker build failed for {service_dir}\n{result.stdout}")
