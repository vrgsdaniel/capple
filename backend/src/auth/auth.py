from src.errors import InternalServerException, NotFoundException
from src.utils.logger import logger as log
from src.settings import get_auth_settings
from supabase import create_client, Client


class Auth:
    def __init__(self, token: str):
        settings = get_auth_settings()
        self.client: Client = create_client(settings.url, settings.service_role_key)
        self.token = token

    async def get_current_user(self):
        token = self.token

        try:
            response = self.client.auth.get_user(token)
            if not response.user:
                log.error("No user found for the provided token.")
                raise NotFoundException("No user found for the provided token.")
            return response.user
        except Exception:
            log.error("Failed to fetch user information.")
            raise InternalServerException("Failed to fetch user information.")
