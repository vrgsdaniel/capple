from src.errors import InternalServerException, NotFoundException
from src.utils.logger import logger as log
from supabase import AsyncClient
from supabase_auth.errors import AuthApiError
from supabase_auth.types import User


class Auth:
    def __init__(self, client: AsyncClient, token: str):
        self.client = client
        self.token = token

    async def get_current_user(self) -> User:
        try:
            response = await self.client.auth.get_user(self.token)
            if not response.user:
                raise NotFoundException("No user found for the provided token.")
            return response.user
        except NotFoundException:
            log.error("No user found for the provided token.")
            raise
        except AuthApiError:
            log.exception("Invalid or expired token")
            raise NotFoundException("Invalid token")
        except Exception as e:
            log.exception("Failed to fetch user information")
            raise InternalServerException("Failed to fetch user information.") from e
