import json
from functools import lru_cache
from typing import Annotated, Any, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EchoDaily API"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./data/echodaily.db"
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["*"])
    wechat_app_id: str | None = None
    wechat_app_secret: str | None = None
    auth_session_days: int = Field(default=30, ge=1, le=365)
    tencentcloud_secret_id: str | None = None
    tencentcloud_secret_key: str | None = None
    tencentcloud_app_id: str | None = None
    tencentcloud_soe_app_id: str | None = None
    tencentcloud_soe_region: str = "ap-guangzhou"
    tencentcloud_soe_transport: Literal["new_websocket", "legacy_sdk"] = "new_websocket"
    tencentcloud_soe_server_engine_type: str = "16k_en"
    tencentcloud_soe_score_coeff: float = Field(default=3.0, ge=1.0, le=4.0)
    tencentcloud_soe_req_timeout_seconds: int = Field(default=30, ge=5, le=120)

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
            if stripped.startswith("["):
                parsed = json.loads(stripped)
                if not isinstance(parsed, list):
                    raise TypeError("CORS_ORIGINS JSON must decode to a list of strings.")
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in stripped.split(",") if item.strip()]
        raise TypeError("CORS_ORIGINS must be a string or a list of strings.")

    @field_validator(
        "wechat_app_id",
        "wechat_app_secret",
        "tencentcloud_secret_id",
        "tencentcloud_secret_key",
        "tencentcloud_app_id",
        "tencentcloud_soe_app_id",
        mode="before",
    )
    @classmethod
    def normalize_optional_string(cls, value: Any) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @field_validator("tencentcloud_soe_region", mode="before")
    @classmethod
    def normalize_tencentcloud_region(cls, value: Any) -> str:
        if value is None:
            return "ap-guangzhou"
        stripped = str(value).strip()
        return stripped or "ap-guangzhou"

    @field_validator("tencentcloud_soe_server_engine_type", mode="before")
    @classmethod
    def normalize_tencentcloud_server_engine_type(cls, value: Any) -> str:
        if value is None:
            return "16k_en"
        stripped = str(value).strip()
        return stripped or "16k_en"

    @model_validator(mode="after")
    def validate_tencentcloud_credentials(self) -> "Settings":
        has_secret_id = self.tencentcloud_secret_id is not None
        has_secret_key = self.tencentcloud_secret_key is not None
        if has_secret_id != has_secret_key:
            raise ValueError(
                "TENCENTCLOUD_SECRET_ID and TENCENTCLOUD_SECRET_KEY must be set together."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
