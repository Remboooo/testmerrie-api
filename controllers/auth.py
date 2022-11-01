from auth.discordauth import DiscordAuth
from sprong import sprongbean, SprongController, mapping, json_endpoint, Request, BadRequest


@sprongbean
class AuthController(SprongController):
    def __init__(self, discord_auth: DiscordAuth):
        self.discord_auth = discord_auth

    @mapping(r"^/v1/token/?$")
    @json_endpoint
    def token(self, req: Request, start_response):
        code = req.get_query_param("code", required=True)
        redirect_uri = req.get_query_param("redirect_uri", required=True)
        return self.discord_auth.exchange_code_for_token(code, redirect_uri)

    @mapping(r"^/v1/refresh-token/?$")
    @json_endpoint
    def refresh_token(self, req: Request, start_response):
        refresh_token = req.get_query_param("refresh_token", required=True)
        return self.discord_auth.refresh_token(refresh_token)

    @mapping(r"^/v1/auth/?$")
    @json_endpoint
    def auth(self, req: Request, start_response):
        auth = self.discord_auth.authenticate(req)
        return {"user": auth.user, "member_of": auth.member_of, "token": auth.testmerrie_token}

    @mapping(r"^/auth-check?$")
    def auth_check(self, req: Request, start_response):
        self.discord_auth.authenticate(req)
        start_response("200 OK", [])

