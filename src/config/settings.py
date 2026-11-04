from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # API Configuration
    project_name: str = "Urja Meter Ops API Service"
    version: str = "1.0.0"
    api_v1_str: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    environment: str = "production"

    # Upstream Urja Portal Configuration
    upstream_portal_url: str = Field(
        default="https://urja-ops.flockenergy.tech",
        description="Base URL of the upstream Urja Meter Ops portal"
    )
    upstream_username: str = Field(
        default="",
        description="Upstream portal username or email loaded from environment"
    )
    upstream_password: str = Field(
        default="",
        description="Upstream portal password loaded from environment"
    )
    upstream_timeout_seconds: float = 30.0
    upstream_max_retries: int = 3
    upstream_retry_backoff_factor: float = 0.5

    # Security & API Authentication
    api_key_secret: str = Field(
        default="urja_ops_secret_api_key_2026",
        description="Shared secret API key required by external consumers"
    )
    api_key_header_name: str = "X-API-Key"

    # Cache TTLs (seconds)
    cache_ttl_meters_seconds: int = 300
    cache_ttl_locations_seconds: int = 600
    cache_ttl_summary_seconds: int = 120
    cache_ttl_energy_seconds: int = 120


settings = Settings()
