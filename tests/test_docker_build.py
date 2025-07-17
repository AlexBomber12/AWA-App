import glob
import os
import shutil
import subprocess

import pytest


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_build_all_service_images() -> None:
    for df in glob.glob("services/*/Dockerfile"):
        if "llm_server" in df and not os.getenv("CUDA_VISIBLE_DEVICES"):
            continue
        subprocess.run(["docker", "build", "--file", df, ".", "-t", "awa-tmp"], check=True)
