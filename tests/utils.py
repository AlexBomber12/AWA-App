from alembic.config import CommandLine, Config


async def run_migrations() -> None:
    cfg = Config("alembic.ini")
    CommandLine().run_cmd(cfg, ["upgrade", "head"])
