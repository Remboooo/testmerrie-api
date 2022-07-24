from auth.discordauth import DiscordAuth
from sprong import sprongbean, SprongController, mapping, json_endpoint


@sprongbean
class AuthController(SprongController):
    def __init__(self, discord_auth: DiscordAuth):
        self.discord_auth = discord_auth

    @mapping(r"^/v1/auth/?$")
    @json_endpoint
    def handle(self, env, start_response):
        auth = self.discord_auth.authenticate(env)
        return {"user": auth.user, "member_of": auth.member_of}
