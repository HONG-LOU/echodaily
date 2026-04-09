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

如果要启用真实口语评测，还需要同时确认：

```bash
export TENCENTCLOUD_SECRET_ID=你的SecretId
export TENCENTCLOUD_SECRET_KEY=你的SecretKey
docker compose up -d --build
```

- 当前后端默认对接的是「口语评测（新版本）」WebSocket 接口
- 若未显式配置 `TENCENTCLOUD_APP_ID`，后端会用当前密钥自动调用 CAM `GetUserAppId` 获取腾讯云账号 AppId
- 若你是历史老账号，要继续使用旧版 `soe.tencentcloudapi.com` 接口，可把 `TENCENTCLOUD_SOE_TRANSPORT=legacy_sdk`
- 默认引擎类型是 `16k_en`，可用 `TENCENTCLOUD_SOE_SERVER_ENGINE_TYPE` 覆盖
- 腾讯云账号已开通「口语评测（新版本）」资源
- 账号未欠费、未被隔离
- `TENCENTCLOUD_SOE_APP_ID` 仅旧版 SDK 路径需要

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
- 当前评测链路默认接入腾讯云「口语评测（新版本）」；若购买的是新版资源包，不需要再走旧版 `soe.tencentcloudapi.com`。
