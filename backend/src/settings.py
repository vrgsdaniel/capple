from functools import lru_cache
from typing import Literal
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "capple"
    env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8080
    opentelemetry: bool = False
    otel_exporter_endpoint: str = "https://otlp-gateway-prod-<region>.grafana.net/otlp/v1/traces"
    otel_exporter_headers: str = "Authorization=Basic <base64(instanceId:token)>"
    openapi_version: str = "3.0.2"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(";") if origin.strip()]


class SupaBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SUPABASE_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    url: str
    service_role_key: str


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLM_", env_file=".env", env_file_encoding="utf-8", extra="ignore")
    provider: Literal["openai", "azure"] = "openai"
    langsmith_api_key: str = ""
    langsmith_tracing: bool = True
    langsmith_project: str = "capple"
    stream: bool = True
    temperature: float = 0.3
    max_retries: int = 2
    intent_confidence_threshold: float = 0.7

    # OpenAI
    open_ai_model: str = "gpt-4o-mini"
    open_ai_base_url: str | None = None
    open_ai_api_key: SecretStr = SecretStr("replace-with-openai-api-key")
    open_ai_free_models_only: bool = False

    # Azure OpenAI
    azure_openai_endpoint: str = "https://your-resource.openai.azure.com"
    azure_deployment: str = "gpt-4o-mini"
    open_ai_version: str = "2024-10-21"
    azure_openai_api_key: SecretStr = SecretStr("replace-with-azure-openai-api-key")


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_llm_settings() -> LLMSettings:
    return LLMSettings()


@lru_cache
def get_supabase_settings() -> SupaBaseSettings:
    return SupaBaseSettings()
