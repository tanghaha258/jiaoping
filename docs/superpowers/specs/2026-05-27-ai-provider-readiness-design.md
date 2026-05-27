# AI Provider Readiness Design

## Goal

Make AI provider configuration observable before real 桂教通 or domestic model calls are enabled.

Administrators should be able to open AI 智能体治理, see whether each agent is ready to run, and understand what is missing without triggering an external model request.

## Scope

This batch adds a read-only readiness check for one AI agent:

`GET /api/v1/ai/agents/{agent_id}/readiness`

The endpoint checks local configuration and provider registry state. It does not call upstream model APIs.

## Response Shape

```json
{
  "agent_id": "string",
  "provider": "openai_compatible_local",
  "status": "ready",
  "mode": "api",
  "label": "配置可运行",
  "summary": "Provider 前置配置完整，已具备发起调用条件。",
  "checks": [
    {
      "key": "endpoint",
      "label": "接口端点",
      "status": "ok",
      "message": "已配置 endpoint"
    }
  ],
  "actions": [
    {
      "label": "在后端环境变量中配置真实密钥",
      "field": "api_key_env"
    }
  ]
}
```

Status values:

- `ready`: configuration can be used by the local gateway.
- `manual_required`: provider is intentionally manual, such as `gjt_link` or `manual_import`.
- `not_configured`: required local configuration is missing.
- `unsupported`: provider is not registered in the gateway.

Check status values:

- `ok`
- `warning`
- `error`

## Provider Rules

`mock`:

- Always `ready`.
- No external endpoint or secret required.

`gjt_api`:

- Requires endpoint from agent config or environment.
- Requires agent identifier from agent config or environment.
- API key is recommended. Missing key produces `warning`, not `error`, because some official platforms may use school-side SSO or IP allowlists.

Domestic/OpenAI-compatible providers:

- `openai_compatible_local`
- `qwen_agent`
- `deepseek_agent`
- `zhipu_agent`
- `doubao_agent`
- `qianfan_agent`
- `spark_agent`
- `kimi_agent`

Rules:

- Requires endpoint from agent config or `OPENAI_COMPATIBLE_API_BASE_URL`.
- Requires model from agent config or `OPENAI_COMPATIBLE_MODEL`.
- Requires a key source: `api_key_env`, config `api_key`, or `OPENAI_COMPATIBLE_API_KEY`.
- If `api_key_env` is present but the environment variable is missing, status is `not_configured`.
- If a raw `api_key` is present in config, status can be `ready` but must include a warning telling admins to move it to an environment variable.

`gjt_link` and `manual_import`:

- Status is `manual_required`.
- Explain that the workflow needs manual copy/paste and teacher adoption.

## Frontend

Update `/admin/ai-agents`:

- Add a readiness column with tags.
- Add a "自检" action button per row.
- Show readiness summary in the detail drawer.
- Add a small readiness panel explaining endpoint/model/key requirements.

The page should use clear Chinese labels:

- `配置自检`
- `配置可运行`
- `缺少配置`
- `需要人工回填`
- `接口端点`
- `模型标识`
- `密钥来源`
- `环境变量未设置`

## Non-Goals

- Do not call 桂教通 or domestic model APIs in this batch.
- Do not store or display real secrets.
- Do not change the lesson-plan draft workflow.
- Do not make AI output publish directly to students.

## Verification

- Backend tests cover ready, not configured, manual required, unsupported, missing-agent, and role blocking.
- Frontend static tests cover the new page copy.
- Browser smoke verifies `/admin/ai-agents` renders readiness labels and the self-check action.

