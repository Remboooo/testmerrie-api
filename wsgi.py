import logging
import os
from argparse import ArgumentParser

import yaml

from controllers.auth import AuthController
from controllers.streams import StreamsController
from sprong import SprongApplication
from sprong.beans import SprongBeanRepo

LOGGER = logging.getLogger()
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class Bami(SprongApplication):
    def __init__(self):
        super().__init__()

        with open(os.path.join(SCRIPT_DIR, "config.yaml"), 'r') as f:
            self.config = yaml.safe_load(f)

        self.repo = SprongBeanRepo()
        ome_config = self.config["ovenMediaEngine"]
        discord_config = self.config["discord"]

        self.repo.register(ome_config, name="ome_config")
        self.repo.register(discord_config, name="discord_config")

        self.add_controller(self.repo.get(StreamsController))
        self.add_controller(self.repo.get(AuthController))


application = Bami()

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    argparse = ArgumentParser()
    argparse.add_argument("-p", "--port", type=int, default=8080, help="Server port")
    argparse.add_argument("-H", "--host", default="127.0.0.1", help="Serve address")
    argparse.add_argument("-v", "--verbose", action='store_true', help="Verbose mode (debug logging)")
    args = argparse.parse_args()
    port = args.port
    host = args.host

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    with make_server(host, port, application) as httpd:
        print(f"Serving on {host}:{port}")
        httpd.serve_forever()
else:
    logging.basicConfig()
