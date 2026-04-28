from functools import lru_cache
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
    cors_origins: list[str] = ["http://localhost:5173"]


class SupaBaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SUPABASE_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    url: str
    service_role_key: str


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_supabase_settings() -> SupaBaseSettings:
    return SupaBaseSettings()
