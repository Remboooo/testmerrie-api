import functools
import json
import logging
import re
import sys
from collections import defaultdict

LOGGER = logging.getLogger(__name__)

MAPPINGS = defaultdict(list)

DEFAULT_HEADERS = [
    ('Access-Control-Allow-Origin', '*'),
    ('Access-Control-Allow-Headers', '*')
]

JSON_HEADERS = [
    ('Content-Type', 'application/json; charset=utf-8')
]


class BadRequest(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Unauthorized(Exception):
    def __init__(self, msg):
        super().__init__(msg)


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
        result = func(self, environ, start_response, *args, **kwargs)
        start_response('200 OK', DEFAULT_HEADERS + JSON_HEADERS)
        return json.dumps(result).encode('utf-8')
    return wrapper


class SprongController:
    def get_url_pattern_mappings(self):
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
        start_response('404 Not Found', DEFAULT_HEADERS + JSON_HEADERS)
        return json.dumps({"message": "The requested endpoint does not exist"})

    def handle(self, environ, start_response):
        try:
            path = environ['PATH_INFO']
            if path.endswith('/'):
                path = path[:-1]

            for pattern, controller, handler in self.mappings:
                if pattern.fullmatch(path):
                    if environ['REQUEST_METHOD'] == 'OPTIONS':
                        return self.preflight_response(environ, start_response)
                    else:
                        return handler(controller, environ, start_response)

            return self.not_found(environ, start_response)

        except BadRequest as e:
            start_response('400 Bad Request', DEFAULT_HEADERS + JSON_HEADERS)
            return json.dumps({"message": str(e)}).encode('utf-8')
        except Unauthorized as e:
            start_response('401 Unauthorized', DEFAULT_HEADERS + JSON_HEADERS)
            return json.dumps({"message": str(e)}).encode('utf-8')
        except Exception as e:
            LOGGER.error("Handler threw unhandled exception", exc_info=sys.exc_info())
            start_response('500 Internal Server Error', DEFAULT_HEADERS + JSON_HEADERS)
            return json.dumps({"message": str(e)}).encode('utf-8')

    def preflight_response(self, environ, start_response):
        start_response('204 OK', DEFAULT_HEADERS + JSON_HEADERS)
