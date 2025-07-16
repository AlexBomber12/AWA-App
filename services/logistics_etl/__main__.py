import asyncio

from .cron import start

if __name__ == "__main__":
    start()
    asyncio.get_event_loop().run_forever()
