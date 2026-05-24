from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
import pytest


class ChatApiIntegrationSettings(BaseSettings):
    use_real_db: bool = False
    use_real_chatbot: bool = False
    use_real_auth: bool = False
    auth_token: str = ""
    user_id: str = "00000000-0000-0000-0000-000000000000"

    model_config = SettingsConfigDict(
        env_prefix="CAPPLE_TEST_",
        extra="ignore",
    )


@pytest.fixture(scope="session")
def integration_settings() -> ChatApiIntegrationSettings:
    return ChatApiIntegrationSettings()


@pytest.fixture(autouse=True)
def _validate_auth_settings(integration_settings: ChatApiIntegrationSettings):
    if integration_settings.use_real_auth and not integration_settings.auth_token:
        pytest.skip("Set CAPPLE_TEST_AUTH_TOKEN when CAPPLE_TEST_USE_REAL_AUTH=true.")
