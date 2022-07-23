import logging
import os

import yaml

from controllers.streams import LegacyApi, StreamsController
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

        self.repo.register(ome_config, name="ome_config")

        self.add_controller(self.repo.get(LegacyApi))
        self.add_controller(self.repo.get(StreamsController))


application = Bami()

if __name__ == '__main__':
    print(application({"PATH_INFO": "/v1/streams"}, lambda *args: print(args)))
    print(application({"PATH_INFO": "/"}, lambda *args: print(args)))
    print(application({"PATH_INFO": "/derp"}, lambda *args: print(args)))
