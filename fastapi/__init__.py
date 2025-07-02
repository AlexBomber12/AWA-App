import types


class FastAPI:
    def __init__(self, *args, **kwargs):
        self.state = types.SimpleNamespace()

    def on_event(self, event):
        def decorator(func):
            return func

        return decorator

    def post(self, path, *args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def get(self, path, *args, **kwargs):
        def decorator(func):
            return func

        return decorator
