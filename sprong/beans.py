from inspect import isclass, signature, Parameter

BEAN_CREATORS = {}


class BeanNotFoundException(Exception):
    def __init__(self, name):
        super(BeanNotFoundException, self).__init__(f"Could not find way to create bean with name {name}")


class BeanInstantiationException(Exception):
    def __init__(self, msg, path):
        super().__init__(f"{msg}. Required in instantiation of {' -> '.join(path)}.")


def sprongbean(cls):
    if cls not in BEAN_CREATORS:
        BEAN_CREATORS[cls.__name__] = cls
    return cls


class SprongBeanRepo:
    def __init__(self):
        self.singletons = {}
        self.register(self)

    def register(self, instance, name=None):
        self.singletons[name or instance.__class__.__name__] = instance

    def get(self, *classes_or_names, path=None):
        names = [v.__name__ if isclass(v) else v for v in classes_or_names]

        for name in names:
            if name in self.singletons:
                return self.singletons[name]
            if path and name in path:
                raise BeanInstantiationException(f"Circular dependency: {' / '.join(names)}", path)

        creator = None
        creator_name = None
        for name in names:
            if name in BEAN_CREATORS:
                creator = BEAN_CREATORS[name]
                creator_name = name
                break

        if creator is None:
            raise BeanInstantiationException(
                f"Bean not found: {' / '.join(names)}",
                path or []
            )

        args = []
        kwargs = {}
        for param in signature(creator).parameters.values():
            if param.default != Parameter.empty or param.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
                continue

            param_names = [param.name]
            if param.annotation != Parameter.empty:
                param_names.append(param.annotation.__name__)

            val = self.get(*param_names, path=[*(path or []), creator_name])
            if param.kind == Parameter.POSITIONAL_ONLY:
                args.append(val)
            else:
                kwargs[param.name] = val

        new_bean = creator(*args, **kwargs)
        self.register(new_bean)
        return new_bean
