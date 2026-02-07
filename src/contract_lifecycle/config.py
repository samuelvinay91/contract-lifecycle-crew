"""Configuration management for the Contract Lifecycle Crew."""

from __future__ import annotations

from common.config import Settings as BaseSettings


class Settings(BaseSettings):
    """Contract Lifecycle Crew configuration.

    Inherits common provider keys and infrastructure settings from
    ``common.config.Settings`` and adds contract-lifecycle-specific options.
    """

    # Service identity
    service_name: str = "contract-lifecycle-crew"
    service_version: str = "0.1.0"
    host: str = "0.0.0.0"
    port: int = 8014

    # LLM configuration
    default_model: str = "gpt-4o-mini"

    # Contract lifecycle settings
    auto_approve_threshold: str = "low"
    max_negotiation_rounds: int = 3

    # Session management
    session_ttl_seconds: int = 3600


def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
