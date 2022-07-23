import functools
import json
import logging
import re
import sys
from collections import defaultdict

LOGGER = logging.getLogger(__name__)

MAPPINGS = defaultdict(list)


def mapping(route):
    class Decorator:
        def __init__(self, fn):
            self.fn = fn

        def __set_name__(self, owner, name):
            LOGGER.info(f"Routing {route} to {owner.__name__}.{name}")
            MAPPINGS[owner].append((route, self.fn))
    return Decorator


def json_endpoint(func):
    @functools.wraps(func)
    def wrapper(self, environ, start_response, *args, **kwargs):
        try:
            result = func(self, environ, start_response, *args, **kwargs)
            start_response('200 OK', [('Content-Type', 'application/json; charset=utf-8')])
            json.dumps(result).encode('utf-8')
        except Exception as e:
            start_response('500 oops', [('Content-Type', 'application/json; charset=utf-8')])
            return json.dumps({"message": str(e)}).encode('utf-8')
    return wrapper


class Controller:
    def get_url_patterns(self):
        return MAPPINGS[self.__class__]


class SprongApplication:
    def __init__(self):
        self.mappings = []

    def __call__(self, environ, start_response):
        return self.handle(environ, start_response)

    def add_controller(self, *controllers):
        self.mappings.extend([
            (re.compile(pattern), controller, handler)
            for controller in controllers
            for pattern, handler in MAPPINGS.get(controller.__class__, [])
        ])

    def not_found(self, environ, start_response):
        start_response('404 Not Found', [('Content-Type', 'application/json; charset=utf-8')])
        return json.dumps({"message": "The requested endpoint does not exist"})

    def handle(self, environ, start_response):
        try:
            path = environ['PATH_INFO']
            if path.endswith('/'):
                path = path[:-1]

            for pattern, controller, handler in self.mappings:
                if pattern.fullmatch(path):
                    return handler(controller, environ, start_response)

            return self.not_found(environ, start_response)

        except Exception as e:
            LOGGER.error("Handler threw unhandled exception", exc_info=sys.exc_info())
            start_response('500 oops', [('Content-Type', 'application/json; charset=utf-8')])
            return json.dumps({"message": str(e)}).encode('utf-8')