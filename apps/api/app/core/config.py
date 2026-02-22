from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://localops:localops@localhost:5432/localops"
    redis_url: str = "redis://localhost:6379/0"
    api_key: str = "localops-dev-key"
    artifact_root: str = "/workspace/data"
    sandbox_image: str = "localops-sandbox-runner:latest"
    api_base_url: str = "http://localhost:8000"


settings = Settings()
