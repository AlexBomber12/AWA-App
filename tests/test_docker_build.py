import os
import pathlib
import shutil
import subprocess

import pytest


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_build_all_service_images() -> None:
    for df in pathlib.Path("services").glob("*/Dockerfile"):
        service_dir = df.parent
        if service_dir.name == "llm_server" and not os.getenv("CUDA_VISIBLE_DEVICES"):
            continue
        subprocess.run(["docker", "build", str(service_dir), "-t", "awa-tmp"], check=True)
