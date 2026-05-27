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

4. 打开运行地址：

   - Teacher/Admin UI: `http://127.0.0.1:3000`
   - API health: `http://127.0.0.1:8000/api/v1/health`
   - API readiness: `http://127.0.0.1:8000/api/v1/health/ready`

默认试运行账号：

| Role | Username | Password |
| --- | --- | --- |
| System admin | `admin` | `admin123` |
| Teacher | `teacher001` | `password` |
| Student | `student001` | `password` |

试运行或正式部署前必须修改 `JWT_SECRET` 和默认账号密码。

## Docker Trial

Docker 试运行使用已有 `deploy/docker-compose.yml`，包含 PostgreSQL、后端 API 和前端静态站点。

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

正式部署时请把数据库密码、`JWT_SECRET`、CORS 域名和对外访问域名替换成真实值。

## SQLite Backup

本地 SQLite 试运行可以从项目根目录创建带时间戳的备份：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/backup-sqlite.ps1
```

可选参数：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/backup-sqlite.ps1 `
  -DatabasePath "backend/app.db" `
  -BackupDir "backups"
```

脚本会优先读取 `backend/.env` 中的 `DATABASE_URL`。如果没有配置 SQLite 路径，则默认备份 `backend/app.db`。

## SQLite Restore

恢复 SQLite 数据库前，请先停止后端服务。然后从指定备份恢复：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/restore-sqlite.ps1 `
  -BackupPath "backups/app-20260525-120000.db"
```

默认情况下，恢复脚本会先在当前数据库旁边创建 `app.pre-restore-YYYYMMDD-HHMMSS.db` 安全备份。只有在已经单独确认有可用备份时，才使用 `-SkipSafetyBackup`。

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
- 国内主流模型或本地网关优先走 OpenAI-compatible 适配器：配置 `OPENAI_COMPATIBLE_API_BASE_URL`、`OPENAI_COMPATIBLE_API_KEY`、`OPENAI_COMPATIBLE_MODEL` 后，在管理端 AI 智能体中选择 `OpenAI兼容本地网关`、`通义千问`、`DeepSeek`、`智谱GLM`、`豆包`、`百度千帆`、`讯飞星火` 或 `Kimi` 等 Provider。真实密钥只放后端环境变量，不写入浏览器可见 JSON。
