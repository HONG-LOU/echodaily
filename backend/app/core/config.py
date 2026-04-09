from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EchoDaily MVP API"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./data/echodaily.db"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    wechat_app_id: str | None = None
    wechat_app_secret: str | None = None
    auth_session_days: int = Field(default=30, ge=1, le=365)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return ["*"]
            if stripped == "*":
                return ["*"]
            return [item.strip() for item in stripped.split(",") if item.strip()]
        raise TypeError("CORS_ORIGINS must be a string or a list of strings.")

    @field_validator("wechat_app_id", "wechat_app_secret", mode="before")
    @classmethod
    def normalize_optional_secret(cls, value: Any) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None


@lru_cache
def get_settings() -> Settings:
    return Settings()
