import logging
import os

import yaml

from controllers.auth import DiscordAuthController
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
        discord_config = self.config["discord"]

        self.repo.register(ome_config, name="ome_config")
        self.repo.register(discord_config, name="discord_config")

        self.add_controller(self.repo.get(LegacyApi))
        self.add_controller(self.repo.get(StreamsController))
        self.add_controller(self.repo.get(DiscordAuthController))


application = Bami()

if __name__ == '__main__':
    print(application({"PATH_INFO": "/v1/discord-auth"}, lambda *args: print(args)))
