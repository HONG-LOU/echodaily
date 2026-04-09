from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class WechatLoginRequestSchema(BaseModel):
    code: str = Field(min_length=1, max_length=128)
    nickname: str | None = Field(default=None, min_length=1, max_length=80)
    avatar_url: str | None = Field(default=None, max_length=512)
    city: str | None = Field(default=None, max_length=80)
    bio: str | None = Field(default=None, max_length=160)

    model_config = ConfigDict(extra="forbid", strict=True)


class AuthenticatedUserSchema(BaseModel):
    id: str
    nickname: str
    avatar_symbol: str
    avatar_url: str | None
    city: str
    bio: str

    model_config = ConfigDict(from_attributes=True)


class WechatLoginResponseSchema(BaseModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_at: datetime
    is_new_user: bool
    user: AuthenticatedUserSchema

    model_config = ConfigDict(from_attributes=True)
