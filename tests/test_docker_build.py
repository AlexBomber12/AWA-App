import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_build_service_images() -> None:
    for dockerfile in Path("services").glob("*/Dockerfile"):
        subprocess.run(
            [
                "docker",
                "build",
                dockerfile.parent.as_posix(),
                "-t",
                "tmp",
            ],
            check=True,
        )
