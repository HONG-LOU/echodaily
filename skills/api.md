---
name: api-design
description: FastAPI 接口设计规范，包含 RESTful 路由、Pydantic v2 校验与全局异常处理。
---

# 🌐 API 设计与 Pydantic v2 规范

你精通 RESTful API 设计和 FastAPI/Pydantic v2 高级特性。

## Pydantic v2 (Schema) 规范
- 进出分离：严格区分 `CreateSchema`, `UpdateSchema`, `ResponseSchema`。
- 配置字典：使用 `model_config = ConfigDict(from_attributes=True)` 替代 v1 的 `orm_mode`。
- 字段验证：充分利用 `Field`, `EmailStr`, `HttpUrl` 以及 `@field_validator` 进行数据前置校验。

## RESTful 路由规则
- 路径全小写，使用复数名词 (如 `/api/v1/users/{user_id}`)。
- 动词与方法对应：
  - `GET /items`: 列表 (支持分页 limit/offset)
  - `GET /items/{id}`: 详情
  - `POST /items`: 创建 (返回 201)
  - `PATCH /items/{id}`: 局部更新 (优先于 PUT)
  - `DELETE /items/{id}`: 删除 (返回 204)

## 异常与响应处理
- **避免隐式返回异常**：业务逻辑抛出自定义异常（如 `UserNotFoundError`）。
- **全局异常拦截**：在 FastAPI `exception_handlers` 中捕获自定义异常并转换为标准 HTTP 响应格式。
- **标准返回结构**：除非与前端另有约定，优先直接返回业务 JSON，依赖 HTTP 状态码表示成败，不盲目包裹一层 `{code: 200, data: ...}`（遵循标准 REST）。

## ✅ 提交前必做检查（与 CI 对齐）
- `uv run mypy . --no-error-summary`
- `uv run ruff check . --output-format=full`
- `uv run ruff format .`