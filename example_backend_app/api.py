"""Example backend app API"""


class ExampleAPI:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def hello(self):
        return f'Hello world from example_backend_app! (kwargs: {self.kwargs})'
