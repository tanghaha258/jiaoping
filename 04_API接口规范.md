# 04 API 接口规范

## 基础约定

后端统一前缀：

```text
/api/v1
```

数据格式：

- 请求体：JSON，文件上传除外。
- 响应体：JSON。
- 时间格式：ISO 8601，例如 `2026-05-21T10:00:00+08:00`。
- 字段命名：JSON 使用 `snake_case`。
- HTTP 状态码与业务 `code` 同时使用。

## 统一响应

成功：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "trace_id": "req_20260521100000001"
}
```

失败：

```json
{
  "code": 40001,
  "message": "invalid username or password",
  "data": null,
  "trace_id": "req_20260521100000002"
}
```

分页：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

## 认证规范

请求头：

```http
Authorization: Bearer <access_token>
```

Token 策略：

- Access Token：默认 30 分钟。
- Refresh Token：默认 7 天。
- 刷新后旧 refresh token 应失效或进入轮换状态。
- 退出登录时服务端记录 token 撤销状态。

## 错误码

| 范围 | 含义 |
| --- | --- |
| 0 | 成功 |
| 40000-40999 | 请求参数、认证、权限错误 |
| 41000-41999 | 业务规则错误 |
| 42000-42999 | AI 调用错误 |
| 43000-43999 | 文件错误 |
| 50000-50999 | 服务端错误 |

常用错误：

| code | message | 说明 |
| --- | --- | --- |
| 40001 | invalid credentials | 登录失败 |
| 40002 | token expired | token 过期 |
| 40003 | permission denied | 无权限 |
| 41001 | resource not found | 资源不存在 |
| 41002 | invalid state transition | 状态流转非法 |
| 42001 | ai provider unavailable | AI 服务不可用 |
| 42002 | ai output requires review | AI 输出需审核 |
| 43001 | invalid file type | 文件类型不允许 |

## 核心接口清单

### Auth

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/auth/login` | 登录 |
| POST | `/auth/refresh` | 刷新 token |
| POST | `/auth/logout` | 退出 |
| GET | `/auth/me` | 当前用户 |

登录请求：

```json
{
  "username": "teacher001",
  "password": "password"
}
```

登录响应 `data`：

```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "name": "张老师",
    "role": "teacher",
    "school_id": "uuid"
  }
}
```

### Users

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/users` | 用户列表 |
| POST | `/users` | 创建用户 |
| GET | `/users/{id}` | 用户详情 |
| PATCH | `/users/{id}` | 更新用户 |
| PATCH | `/users/{id}/status` | 启用/停用用户 |

### Schools

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/schools` | 学校列表 |
| POST | `/schools` | 创建学校 |
| GET | `/schools/{id}/classes` | 班级列表 |
| POST | `/schools/{id}/classes` | 创建班级 |
| GET | `/classes/{id}/students` | 学生列表 |

### Projects

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/projects` | 项目列表 |
| POST | `/projects` | 创建项目 |
| GET | `/projects/{id}` | 项目详情 |
| PATCH | `/projects/{id}` | 更新项目 |
| POST | `/projects/{id}/activate` | 启动项目 |
| POST | `/projects/{id}/complete` | 结项 |
| POST | `/projects/{id}/archive` | 归档 |

创建项目请求：

```json
{
  "name": "保护海洋，从我做起",
  "grade": "七年级",
  "subject_ids": ["uuid"],
  "class_ids": ["uuid"],
  "driving_question": "如何减少生活中的海洋污染？",
  "lesson_count": 5,
  "objectives": ["理解海洋生态系统", "完成跨学科调查与表达"]
}
```

### Tasks

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/projects/{project_id}/tasks` | 项目任务列表 |
| POST | `/projects/{project_id}/tasks` | 创建任务 |
| GET | `/tasks/{id}` | 任务详情 |
| PATCH | `/tasks/{id}` | 更新任务 |
| POST | `/tasks/{id}/publish` | 发布任务 |
| POST | `/tasks/{id}/close` | 关闭任务 |
| POST | `/tasks/{id}/submissions` | 学生提交 |
| GET | `/tasks/{id}/submissions` | 提交列表 |

### Rubrics

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/rubrics` | 量规列表 |
| POST | `/rubrics` | 创建量规 |
| GET | `/rubrics/{id}` | 量规详情 |
| PATCH | `/rubrics/{id}` | 更新量规 |

量规结构：

```json
{
  "name": "跨学科探究评价量规",
  "items": [
    {
      "dimension": "探究能力",
      "level_a": "能够提出清晰问题并设计调查方案",
      "level_b": "能够提出问题并参与调查",
      "level_c": "需要在教师帮助下完成调查"
    }
  ]
}
```

### Evaluations

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/evaluations` | 创建评价 |
| GET | `/evaluations` | 评价列表 |
| GET | `/evaluations/{id}` | 评价详情 |
| PATCH | `/evaluations/{id}` | 修改评价 |
| POST | `/evaluations/{id}/confirm` | 教师确认 |

### Resources

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/resources` | 资源列表 |
| POST | `/resources` | 创建资源元数据 |
| POST | `/resources/upload` | 上传文件 |
| GET | `/resources/{id}` | 资源详情 |
| PATCH | `/resources/{id}` | 更新资源 |
| DELETE | `/resources/{id}` | 删除资源 |

### AI Agents

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/ai/agents` | 智能体列表 |
| POST | `/ai/agents` | 创建智能体配置 |
| GET | `/ai/agents/{id}` | 智能体详情 |
| PATCH | `/ai/agents/{id}` | 更新智能体 |
| POST | `/ai/agents/{id}/test` | 测试智能体配置 |

### AI Calls

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/ai/calls` | 发起 AI 调用 |
| GET | `/ai/calls` | 调用记录列表 |
| GET | `/ai/calls/{id}` | 调用详情 |
| POST | `/ai/calls/{id}/import` | 人工回填结果 |
| POST | `/ai/calls/{id}/review` | 审核 AI 输出 |
| POST | `/ai/calls/{id}/adopt` | 采纳输出到业务对象 |

AI 调用请求：

```json
{
  "agent_id": "uuid",
  "scenario": "lesson_plan",
  "project_id": "uuid",
  "input": {
    "grade": "七年级",
    "subjects": ["地理", "生物", "语文"],
    "topic": "保护海洋，从我做起",
    "lesson_count": 5
  }
}
```

### Dashboard

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/dashboard/overview` | 总览统计 |
| GET | `/dashboard/ai-usage` | AI 使用统计 |
| GET | `/dashboard/project-trends` | 项目趋势 |
| GET | `/dashboard/resource-stats` | 资源统计 |

### Audit Logs

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/audit-logs` | 审计日志列表 |
| GET | `/audit-logs/{id}` | 审计详情 |

## 接口冻结规则

- 前后端并行开发前冻结路径、方法、请求字段、响应字段。
- 新增字段默认向后兼容。
- 删除或重命名字段必须更新本文档并通知前后端和测试智能体。
- 所有业务写操作必须记录审计日志。

