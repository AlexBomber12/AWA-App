import types


async def create_pool(dsn):
    return types.SimpleNamespace(
        fetch=lambda q, *a: [], execute=lambda *a, **k: None, close=lambda: None
    )
