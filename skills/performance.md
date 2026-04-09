---
name: performance-optimization
description: 性能优化策略，包含解决 N+1 查询、缓存策略、并发与后台任务。
---

# 🚀 性能优化与并发安全

你是系统性能调优专家，负责预防和解决高并发场景下的瓶颈。

## 数据库级优化
- **消灭 N+1 查询**：
  - 在 SQLAlchemy 中，严格审查关联查询。必须使用 `selectinload()` 或 `joinedload()` 预加载一对多或多对多关系。
- **分页规范**：
  - 数据量较大时，禁止无条件 `SELECT *`。必须提供基于游标 (Cursor Pagination) 或 Limit/Offset 分页。
- **索引**：根据查询频率高的 `WHERE` 和 `ORDER BY` 字段建议建立 B-Tree 或联合索引。

## 计算与 I/O 优化
- **后台任务**：发送邮件、第三方 API 调用、复杂聚合等耗时操作，必须交给 `FastAPI BackgroundTasks` 或异步任务队列（如 Celery, ARQ, Taskiq）。
- **缓存策略**：对于高频不常变动的数据，建议结合 Redis 添加缓存层。
- **并发控制**：涉及库存扣减、余额修改的场景，必须使用数据库的行锁 (`SELECT ... FOR UPDATE`) 或乐观锁，保证数据一致性。

## ✅ 提交前必做检查（与 CI 对齐）
- `uv run mypy . --no-error-summary`
- `uv run ruff check . --output-format=full`
- `uv run ruff format .`