from auth.discordauth import DiscordAuth
from sprong import sprongbean, SprongController, mapping, json_endpoint, Request


@sprongbean
class AuthController(SprongController):
    def __init__(self, discord_auth: DiscordAuth):
        self.discord_auth = discord_auth

    @mapping(r"^/v1/auth/?$")
    @json_endpoint
    def auth(self, req: Request, start_response):
        auth = self.discord_auth.authenticate(req)
        return {"user": auth.user, "member_of": auth.member_of, "token": auth.testmerrie_token}

    @mapping(r"^/auth-check?$")
    def auth_check(self, req: Request, start_response):
        self.discord_auth.authenticate(req)
        start_response("200 OK", [])
