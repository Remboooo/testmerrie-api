import datetime
import logging
import secrets
from dataclasses import dataclass

import requests
from requests import HTTPError

from sprong import sprongbean, Unauthorized, Request


LOGGER = logging.getLogger(__name__)


@dataclass
class CachedToken:
    discord_token: str
    expires: datetime.datetime
    user: dict
    member_of: dict
    testmerrie_token: str


@sprongbean
class DiscordAuth:
    def __init__(self, discord_config):
        self.client_id = discord_config["clientId"]
        self.client_secret = discord_config["clientSecret"]
        self.auth_cache_seconds = discord_config["authCacheSeconds"]
        self.allow_guilds = discord_config["allowGuilds"]
        self.allowed_callback_uris = discord_config["allowedCallbackUris"]
        self.token_cache = {}

    def purge_old_tokens(self):
        for key in list(self.token_cache.keys()):
            if self.token_cache.get(key).expires <= datetime.datetime.utcnow():
                del self.token_cache[key]

    def discord_get(self, path, token):
        result = requests.get(f"https://discord.com/api/{path}", headers={
            "Authorization": token
        })
        result.raise_for_status()
        return result.json()

    def authenticate(self, req: Request):
        discord_token = req.authorization
        tm_token = req.get_query_param("token")

        LOGGER.debug("Req %s tokens '%s'/'%s', token cache size = %d", req, discord_token, tm_token, len(self.token_cache))

        if not discord_token and not tm_token:
            raise Unauthorized("Missing Authorization header")

        self.purge_old_tokens()
        auth = self.token_cache.get(discord_token) or self.token_cache.get(tm_token)
        if auth is not None:
            return auth
        elif discord_token is None:
            raise Unauthorized("Unknown token")

        try:
            me = self.discord_get("/users/@me", discord_token)
        except HTTPError as e:
            if e.response.status_code in (401, 403):
                raise Unauthorized(f"Discord replied: {e.response.reason}")
            else:
                raise e

        member_of = {}
        for guild in self.allow_guilds.keys():
            try:
                member_of[guild] = self.discord_get(f"/users/@me/guilds/{guild}/member", discord_token)
            except HTTPError as e:
                pass

        if not member_of:
            raise Unauthorized("You are not a member of any of the allowed Discord guilds")

        if not any(
                str(role) in member["roles"]
                for guild, member in member_of.items()
                for role in self.allow_guilds[guild]["allowRoles"]
        ):
            raise Unauthorized("You don't have any of the required roles in any of the allowed Discord guilds")

        auth = CachedToken(
            discord_token=discord_token,
            expires=datetime.datetime.utcnow() + datetime.timedelta(seconds=self.auth_cache_seconds),
            user=me,
            member_of=member_of,
            testmerrie_token=secrets.token_urlsafe(16)
        )
        self.token_cache[discord_token] = auth
        self.token_cache[auth.testmerrie_token] = auth
        return auth

    def exchange_code_for_token(self, code, redirect_uri):
        if redirect_uri not in self.allowed_callback_uris:
            raise Unauthorized("Callback URI not allowed")
        result = requests.post(
            f"https://discord.com/api/oauth2/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        result.raise_for_status()
        return result.json()

    def refresh_token(self, refresh_token):
        result = requests.post(
            f"https://discord.com/api/oauth2/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        result.raise_for_status()
        return result.json()
