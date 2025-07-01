import types


class FastAPI:
    def __init__(self):
        self.state = types.SimpleNamespace()

    def on_event(self, event):
        def decorator(func):
            return func

        return decorator

    def post(self, path):
        def decorator(func):
            return func

        return decorator
