import asyncio

from .cron import start


async def _run() -> None:
    start()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(_run())
