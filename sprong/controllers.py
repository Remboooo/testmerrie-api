import functools
import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import AnyStr
from urllib.parse import parse_qs

LOGGER = logging.getLogger(__name__)

MAPPINGS = defaultdict(list)

DEFAULT_HEADERS = [
    ('Access-Control-Allow-Origin', '*'),
    ('Access-Control-Allow-Headers', '*')
]

JSON_HEADERS = [
    ('Content-Type', 'application/json; charset=utf-8')
]


class HttpError(Exception):
    def __init__(self, code, status, msg):
        super().__init__(msg)
        self.code = code
        self.status = status


class BadRequest(HttpError):
    def __init__(self, msg):
        super().__init__(400, "Bad Request", msg)


class Unauthorized(HttpError):
    def __init__(self, msg):
        super().__init__(401, "Unauthorized", msg)


class NotFound(HttpError):
    def __init__(self, msg):
        super().__init__(404, "Not Found", msg)


class InternalServerError(HttpError):
    def __init__(self, msg):
        super().__init__(500, "Internal Server Error", msg)


@dataclass
class Request:
    env: dict

    @property
    def method(self):
        return self.env.get("REQUEST_METHOD")

    @property
    def authorization(self):
        return self.env.get("HTTP_AUTHORIZATION")

    @property
    def query(self):
        return self.env.get("QUERY_STRING")

    @property
    def path(self):
        return self.env.get("PATH_INFO")

    def get_query_param_value_list(self, key) -> list[AnyStr]:
        return parse_qs(self.query).get(key) or []

    def get_query_param(self, key) -> (AnyStr, None):
        val = self.get_query_param_value_list(key)
        if len(val) == 0:
            return None
        else:
            return val[0]


def mapping(route):
    class Decorator:
        def __init__(self, fn):
            self.fn = fn

        def __set_name__(self, owner, name):
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
        new_mappings = [
            (re.compile(pattern), controller, handler)
            for controller in controllers
            for pattern, handler in MAPPINGS.get(controller.__class__, [])
        ]
        for pattern, controller, handler in new_mappings:
            LOGGER.info("Routing %s to %s.%s", pattern.pattern, controller.__class__.__name__, handler.__name__)
        self.mappings.extend(new_mappings)

    def handle(self, environ, start_response):
        req = Request(environ)
        try:
            path = req.path

            for pattern, controller, handler in self.mappings:
                if pattern.fullmatch(path):
                    if req.method == 'OPTIONS':
                        return self.preflight_response(req, start_response)
                    else:
                        try:
                            return handler(controller, Request(env=environ), start_response)
                        except Exception as e:
                            if isinstance(e, HttpError):
                                raise e
                            else:
                                LOGGER.error("Unhandled exception in controller", exc_info=sys.exc_info())
                                raise InternalServerError(str(e))
            else:
                raise NotFound("Requested resource was not found")

        except HttpError as e:
            LOGGER.debug("%s %s %s -> %s %s '%s'", req.method, req.path, req.query, e.code, e.status, str(e))
            start_response(f'{e.code} {e.status}', DEFAULT_HEADERS + JSON_HEADERS)
            return json.dumps({"message": str(e)}).encode('utf-8')

    def preflight_response(self, req: Request, start_response):
        start_response('204 OK', DEFAULT_HEADERS + JSON_HEADERS)
