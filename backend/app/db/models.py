from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(UTC)


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    subtitle: Mapped[str] = mapped_column(String(160))
    pack_name: Mapped[str] = mapped_column(String(80))
    english_text: Mapped[str] = mapped_column(Text)
    translation: Mapped[str] = mapped_column(Text)
    scenario: Mapped[str] = mapped_column(String(160))
    mode_hint: Mapped[str] = mapped_column(String(160))
    blind_box_prompt: Mapped[str] = mapped_column(String(200))
    tags: Mapped[list[str]] = mapped_column(JSON)
    difficulty: Mapped[str] = mapped_column(String(32))
    estimated_seconds: Mapped[int] = mapped_column(Integer)
    poster_blurb: Mapped[str] = mapped_column(String(160))
    theme_tone: Mapped[str] = mapped_column(String(32))
    published_on: Mapped[date] = mapped_column(Date, index=True)


class DailyHomepageMessage(Base):
    __tablename__ = "daily_homepage_messages"

    message_date: Mapped[date] = mapped_column(Date, primary_key=True)
    message_text: Mapped[str] = mapped_column(String(160))
    provider: Mapped[str] = mapped_column(String(32))
    model_name: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    wechat_openid: Mapped[str | None] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=True,
    )
    wechat_unionid: Mapped[str | None] = mapped_column(
        String(128),
        unique=True,
        index=True,
        nullable=True,
    )
    nickname: Mapped[str] = mapped_column(String(80))
    avatar_symbol: Mapped[str] = mapped_column(String(8))
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    total_practices: Mapped[int] = mapped_column(Integer, default=0)
    weekly_minutes: Mapped[int] = mapped_column(Integer, default=0)
    pro_active: Mapped[bool] = mapped_column(Boolean, default=False)
    plan_name: Mapped[str] = mapped_column(String(80))
    weak_sound: Mapped[str] = mapped_column(String(32))
    target_pack: Mapped[str] = mapped_column(String(80))
    focus_tag: Mapped[str] = mapped_column(String(80))
    city: Mapped[str] = mapped_column(String(80))
    bio: Mapped[str] = mapped_column(String(160))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), index=True)
    mode: Mapped[str] = mapped_column(String(32))
    duration_seconds: Mapped[int] = mapped_column(Integer)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_used: Mapped[bool] = mapped_column(Boolean, default=False)
    comparison_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    overall_score: Mapped[int] = mapped_column(Integer)
    pronunciation_score: Mapped[int] = mapped_column(Integer)
    fluency_score: Mapped[int] = mapped_column(Integer)
    intonation_score: Mapped[int] = mapped_column(Integer)
    stress_score: Mapped[int] = mapped_column(Integer)
    completeness_score: Mapped[int] = mapped_column(Integer)
    mistake_count: Mapped[int] = mapped_column(Integer, default=0)
    highlight_words: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    headline: Mapped[str] = mapped_column(String(160))
    encouragement: Mapped[str] = mapped_column(String(220))
    poster_caption: Mapped[str] = mapped_column(String(180))
    poster_theme: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("user_profiles.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
