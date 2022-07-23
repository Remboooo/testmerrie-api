class SingletonRepo:
    def __init__(self):
        self.singletons = {}

    def register(self, instance):
        self.singletons[instance.__class__] = instance

    def get(self, cls):
        return self.singletons[cls]
