from sprong import sprongbean, Controller, mapping, json_endpoint


@sprongbean
class DiscordAuthController(Controller):
    def __init__(self, discord_config):
        self.client_id = discord_config["clientId"]
        self.client_secret = discord_config["clientSecret"]

    @mapping(r"^/v1/discord-auth/?$")
    @json_endpoint
    def handle(self, env, start_response):
        return "hello world"
