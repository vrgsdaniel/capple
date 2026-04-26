from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "capple"
    env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8080
    opentelemetry: bool = False
    otel_exporter_endpoint: str = "https://otlp-gateway-prod-<region>.grafana.net/otlp/v1/traces"
    otel_exporter_headers: str = "Authorization=Basic <base64(instanceId:token)>"
    openapi_version: str = "3.0.2"


@lru_cache
def get_settings() -> Settings:
    return Settings()
