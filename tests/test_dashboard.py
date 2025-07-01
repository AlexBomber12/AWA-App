import os
import shutil
import subprocess
import time

from urllib import request
import pytest

try:
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover - optional dependency
    sync_playwright = None

if os.getenv("PLAYWRIGHT_OFFLINE") == "1" or sync_playwright is None:
    pytest.skip("Playwright disabled or unavailable", allow_module_level=True)

if shutil.which("docker") is None:
    pytest.skip("Docker not installed", allow_module_level=True)


def wait_for_server(url: str, timeout: int = 30) -> None:
    for _ in range(timeout):
        try:
            with request.urlopen(url) as resp:  # noqa: S310
                if resp.status < 500:
                    return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("server did not start")


def test_dashboard_local_compose():
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    try:
        wait_for_server("http://localhost:3000")
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception as e:  # pragma: no cover - browser missing
                pytest.skip(f"playwright launch failed: {e}")
            page = browser.new_page()
            page.goto("http://localhost:3000/")
            assert page.title() is not None
            browser.close()
    finally:
        subprocess.run(["docker", "compose", "down"], check=False)
