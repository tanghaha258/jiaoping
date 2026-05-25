# Deployment Guide

## Local Trial

本地试运行适合学校演示、业务验收和数据初始化检查。

1. 准备后端环境：

   ```powershell
   cd backend
   copy .env.example .env
   python -m pip install -r requirements.txt
   ```

2. 准备前端环境：

   ```powershell
   cd frontend
   copy .env.example .env
   npm install
   ```

3. 从项目根目录启动本地试运行：

   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
   ```

4. 打开前端：

   - Teacher/Admin UI: `http://127.0.0.1:3000`
   - API health: `http://127.0.0.1:8000/api/v1/health`
   - Readiness: `http://127.0.0.1:8000/api/v1/health/ready`

默认试运行账号：

| Role | Username | Password |
| --- | --- | --- |
| System admin | `admin` | `admin123` |
| Teacher | `teacher001` | `password` |
| Student | `student001` | `password` |

试运行或正式部署前必须修改 `JWT_SECRET` 和默认账号密码。

## Docker Trial

Docker 试运行使用已有 `deploy/docker-compose.yml`，包含 PostgreSQL、后端 API 和 Nginx 静态站点。

1. 构建前端静态资源：

   ```powershell
   cd frontend
   npm install
   npm run build
   ```

2. 启动容器：

   ```powershell
   cd deploy
   docker compose up -d --build
   ```

3. 检查服务：

   ```powershell
   docker compose ps
   ```

4. 访问：

   - UI: `http://127.0.0.1`
   - API health: `http://127.0.0.1/api/v1/health`
   - API readiness: `http://127.0.0.1/api/v1/health/ready`

正式部署时请把 `deploy/docker-compose.yml` 中的数据库密码、`JWT_SECRET` 和域名配置替换成真实值。

## Smoke Test

本地后端启动后，从项目根目录运行：

```powershell
python scripts/smoke_deploy.py
```

可选环境变量：

```powershell
$env:JIAOPING_API_BASE="http://127.0.0.1:8000/api/v1"
$env:JIAOPING_SMOKE_USERNAME="teacher001"
$env:JIAOPING_SMOKE_PASSWORD="password"
python scripts/smoke_deploy.py
```

烟测会检查：

- API liveness: `/health`
- API readiness: `/health/ready`
- 教师登录与 AI 契约入口：`/ai/contracts`

## Release Check

发布前从项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check-release.ps1
```

该脚本会执行：

- `python -m pytest backend/tests -q`
- `python -m compileall backend\app`
- `npm run build`

## AI Provider Mode

当前一期保持本地契约优先：

- `GJT_API_BASE_URL`、`GJT_API_KEY`、`GJT_AGENT_ID` 为空时使用 `mock` 模式。
- 三个字段都配置后，readiness 会显示 `gjt_api` 模式。
- 正式桂教通 API 文档到位后，只替换 provider 适配器，不改业务工作流和数据库契约。
