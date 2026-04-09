# EchoDaily MVP 快速部署

## 1. 当前线上入口

这台服务器已经通过主机 Nginx 对外暴露，当前公网访问地址是：

```text
https://template-chat.xyz/api/v1
```

已验证健康检查：

```text
GET https://template-chat.xyz/api/v1/health/live
GET https://template-chat.xyz/api/v1/health/ready
```

## 2. 启动后端

在项目根目录执行：

```bash
docker compose up -d --build
```

当前部署方式是：

- Docker 内运行 `PostgreSQL 16`
- 容器内 FastAPI 监听 `8000`
- `docker-compose` 绑定 `127.0.0.1:8000` 和 `127.0.0.1:5432`
- 主机 Nginx 监听 `80`
- Nginx 反向代理到 `127.0.0.1:8000`

首次启用微信登录前，需要在启动命令所在的 shell 中提供：

```bash
export WECHAT_APP_SECRET=你的小程序AppSecret
docker compose up -d --build
```

## 3. 小程序联调

当前小程序默认读取的后端地址已经改为：

```text
https://template-chat.xyz/api/v1
```

你也可以在两处自行切换：

1. 修改 [miniprogram/app.ts](/c:/Users/Administrator/WeChatProjects/miniprogram-1/miniprogram/app.ts) 里的默认地址。
2. 打开小程序「我的」页，在“快速部署配置”里保存新的 API 地址。

## 4. 微信小程序注意事项

当前这个正式入口已经适合：

```text
https://template-chat.xyz/api/v1
```

如果要走微信小程序真机联调、提审或正式发布，还需要同时确认：

- `HTTPS`
- 合法 request 域名
- `template-chat.xyz` 已配置到小程序后台的 request 合法域名
- 服务端证书链完整、可被微信客户端正常校验

## 5. 当前 MVP 范围

- 已完成：首页、练习、报告、挑战、我的五个页面闭环。
- 已完成：FastAPI 后端、微信登录、真实用户会话、挑战与个人中心接口。
- 已完成：Dockerfile、docker-compose、PostgreSQL 持久化目录。
- 当前评测为 MVP 模拟服务，后续可在后端 `AssessmentService` 中替换为真实 ASR / 语音评分能力。
