import os
import shutil
import subprocess
from pathlib import Path

import pytest

DOCKERFILES = list(Path("services").glob("*/Dockerfile"))


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
@pytest.mark.parametrize("dockerfile", DOCKERFILES, ids=lambda p: p.parent.name)
def test_build_service_images(dockerfile: Path) -> None:
    if dockerfile.parent.name == "llm_server" and not os.getenv("CUDA_VISIBLE_DEVICES"):
        pytest.skip("GPU image skipped")
    subprocess.run(["docker", "build", dockerfile.parent.as_posix(), "-t", "tmp"], check=True)
