import asyncio
import os

from aiohttp import web


async def _health(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def _run() -> None:
    app = web.Application()
    app.router.add_get("/health", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner, host="0.0.0.0", port=int(os.getenv("HEALTH_PORT", "8001"))
    )
    await site.start()
    while True:
        await asyncio.sleep(3600)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
