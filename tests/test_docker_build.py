import os
import pathlib
import shutil
import subprocess

import pytest


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_build_all_service_images(tmp_path: pathlib.Path) -> None:
    for df in pathlib.Path("services").glob("*/Dockerfile"):
        service_dir = df.parent
        if service_dir.name == "llm_server" and not os.getenv("CUDA_VISIBLE_DEVICES"):
            continue
        log_file = tmp_path / f"{service_dir.name}.log"
        attempt = 0
        result = subprocess.CompletedProcess([], 1)
        while attempt < 3 and result.returncode != 0:
            attempt += 1
            result = subprocess.run(
                ["docker", "build", str(service_dir), "-t", "awa-tmp"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        log_file.write_text(result.stdout)
        if result.returncode != 0:
            pytest.fail(f"docker build failed for {service_dir} after {attempt} attempts\n{result.stdout}")
