from src.errors import InternalServerException, NotFoundException
from src.utils.logger import logger as log
from src.settings import get_supabase_settings
from supabase import create_client, Client
from functools import lru_cache


@lru_cache
def get_auth_client() -> Client:
    settings = get_supabase_settings()
    return create_client(settings.url, settings.service_role_key)


class Auth:
    def __init__(self, token: str):
        self.client: Client = get_auth_client()
        self.token = token

    async def get_current_user(self):
        try:
            response = self.client.auth.get_user(self.token)
            if not response.user:
                raise NotFoundException("No user found for the provided token.")
            return response.user
        except NotFoundException:
            log.error("No user found for the provided token.")
            raise
        except Exception as e:
            log.exception("Failed to fetch user information")
            raise InternalServerException("Failed to fetch user information.") from e
