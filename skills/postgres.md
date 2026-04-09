---
name: postgres-database
description: PostgreSQL 数据库规范，涵盖 SQLAlchemy 2.0 异步操作、Alembic 迁移与模型设计。
---

# 🗄 PostgreSQL & SQLAlchemy 2.0 规范

你是一个数据库专家，精通 PostgreSQL 和 SQLAlchemy 2.0 的异步生态。

## 核心约定
- **ORM**: SQLAlchemy 2.0+ (强制使用 `AsyncSession` 和 `AsyncEngine`)。
- **迁移**: Alembic。所有表结构变更必须提示生成 migration。
- **模型定义**: 使用 SQLAlchemy 2.0 的 `Mapped` 和 `mapped_column`。

## 模型设计最佳实践
- **主键**: 默认使用 UUID (PostgreSQL 原生 `uuid` 类型)，或具明确业务含义的 ULID/Snowflake ID。
- **时间戳**: 必须使用带时区的时间 `TIMESTAMP WITH TIME ZONE` (`datetime.now(UTC)`)。
- **JSON数据**: 结构化/半结构化扩展字段统一使用 `JSONB`，利用 GIN 索引。
- **软删除**: 视业务需求添加 `deleted_at: Mapped[datetime | None]`，避免硬删除。

## 示例代码风格
```python
from uuid import UUID, uuid4
from datetime import datetime, UTC
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
```

**禁忌**：绝对不要在异步环境中使用同步的 `Session` 或 `.first()`，必须使用 `await session.execute(stmt)` 和 `.scalar_one_or_none()`。

## ✅ 提交前必做检查（与 CI 对齐）
- `uv run mypy . --no-error-summary`
- `uv run ruff check . --output-format=full`
- `uv run ruff format .`