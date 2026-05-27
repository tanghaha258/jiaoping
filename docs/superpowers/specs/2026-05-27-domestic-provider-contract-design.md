# Domestic AI Provider Contract Design

## Goal

Make Phase 10 of the platform provider-neutral for domestic AI agents. 桂教通 remains the competition provider, but the platform should also be able to call domestic OpenAI-compatible or JSON-over-HTTP agents such as 通义千问、DeepSeek、智谱 GLM、豆包、百度千帆、讯飞星火、Kimi, and local gateways without changing teaching workflows.

## Scope

This phase does not require a live upstream key. It hardens the local contract and provider adapter structure so trial deployment can keep using `mock`, while production can switch one AI agent row to `gjt_api` or another domestic provider.

Included:

- Extend local provider identifiers and schemas.
- Add a reusable OpenAI-compatible provider adapter for domestic model gateways.
- Keep 桂教通 as a dedicated JSON-over-HTTP provider.
- Add provider configuration examples and admin-facing guidance.
- Document the 桂教通 agent prompt that the user can manually paste into the GJT creator page.

Out of scope for this phase:

- Storing real API keys in the repository.
- Calling a paid/live upstream during automated tests.
- Allowing AI output to publish directly to students.
- Replacing the existing lesson-plan adoption transaction.

## Provider Identifiers

Supported identifiers should include:

- `mock`
- `gjt_api`
- `gjt_link`
- `manual_import`
- `openai_compatible_local`
- `qwen_agent`
- `deepseek_agent`
- `zhipu_agent`
- `doubao_agent`
- `qianfan_agent`
- `spark_agent`
- `kimi_agent`

Provider identifiers are operational routing values. Business workflows should still only see scenario contracts such as `lesson_plan`.

## Adapter Contract

All providers continue using:

- `AIProviderRequest`
- `AIProviderResult`
- `BaseAIProvider.run`
- `BaseAIProvider.health_check`

Provider adapters may differ in HTTP/auth payload, but they must return the same result shape and keep `requires_review=True`.

## OpenAI-Compatible Provider

Many domestic model gateways support OpenAI-style chat completions. The reusable provider should:

- Read `endpoint`, `api_key`, `api_key_env`, `model`, `timeout_seconds`, and optional `extra` from `request.agent_config`.
- Fallback to environment variables for endpoint/key/model where appropriate.
- Send `messages` with a system prompt instructing strict JSON output.
- Prefer `response_format: { "type": "json_object" }` when configured.
- Extract `choices[0].message.content`.
- Parse JSON when possible.
- Return a failed `AIProviderResult` when endpoint/model/key is missing or JSON parsing fails.
- Never expose raw API keys in metadata.

## 桂教通 Manual Agent Contract

The user can manually create a 桂教通智能体 with this purpose:

> 你是“跨学科教学评一体化平台”的结构化教学方案生成智能体。你只负责根据教师输入生成 JSON 草案，不直接创建项目、发布任务或把内容给学生。平台会在教师审阅采纳后再入库。

Recommended agent name:

```text
跨学科教学方案JSON草案智能体
```

Recommended agent description:

```text
根据初中跨学科主题、年级、班级、学科、课时数、核心素养、评价方式和资源偏好，生成符合平台本地契约的教学方案 JSON 草案。输出只供教师审阅采纳。
```

Recommended system prompt:

```text
你是“跨学科教学评一体化平台”的结构化教学方案生成智能体。

你的任务：
1. 根据教师输入生成初中跨学科教学方案草案。
2. 只输出 JSON，不输出 Markdown、解释文字、代码块或额外寒暄。
3. 输出必须包含 project、tasks、rubric、resources、teacher_notes 五个顶层字段。
4. 生成内容只供教师审阅，不能直接发布给学生。
5. tasks 表示草稿任务，不要写“已发布”。
6. 保持中文、可落地、适合学校真实试运行。

输入字段可能包括：
- theme: 教学主题
- grade: 年级
- subjects: 学科名称列表
- class_names: 班级名称列表
- lesson_count: 课时数
- core_competencies: 核心素养目标
- interdisciplinary_requirements: 跨学科要求
- assessment_preferences: 评价方式偏好
- resource_preferences: 资源偏好
- extra_requirements: 补充说明

输出 JSON schema：
{
  "project": {
    "name": "string",
    "grade": "string",
    "driving_question": "string",
    "lesson_count": 1,
    "objectives": ["string"]
  },
  "tasks": [
    {
      "title": "string",
      "description": "string",
      "task_type": "individual|group|classroom|homework",
      "submit_type": "text|file|url|mixed"
    }
  ],
  "rubric": {
    "name": "string",
    "description": "string",
    "scope": "personal",
    "items": [
      {
        "dimension": "string",
        "weight": 20,
        "level_a": "string",
        "level_b": "string",
        "level_c": "string",
        "level_d": "string"
      }
    ]
  },
  "resources": [
    {
      "title": "string",
      "resource_type": "document|video|link|ai_suggested",
      "url": "",
      "description": "string"
    }
  ],
  "teacher_notes": ["string"]
}

约束：
- tasks 数量建议等于 lesson_count，除非教师要求更少。
- rubric.items 权重总和建议为 100。
- task_type 只能从 individual、group、classroom、homework 中选择。
- submit_type 只能从 text、file、url、mixed 中选择。
- resources 不确定真实 URL 时 url 输出空字符串。
- 不要输出 student_visible、published、status 等会导致直接发布给学生的字段。
```

## Platform Request Payload To GJT

When calling 桂教通, the platform should send:

```json
{
  "agent_id": "configured-gjt-agent-id",
  "scenario": "lesson_plan",
  "input": {
    "theme": "海洋生态保护",
    "grade": "七年级",
    "subjects": ["地理", "生物"],
    "class_names": ["七年级(1)班"],
    "lesson_count": 3,
    "core_competencies": ["问题解决", "证据表达"],
    "interdisciplinary_requirements": "融合地理与生物证据。",
    "assessment_preferences": "过程性评价与成果评价结合。",
    "resource_preferences": "任务单、资料包、展示模板。",
    "extra_requirements": "贴近钦州本地海洋资源。"
  },
  "output_format": "json"
}
```

The current provider may also send internal IDs in `input`; the normalization layer keeps subject/class IDs from the original teacher form.

## Error Handling

- Missing endpoint/model/key should produce `success=False` with a clear error.
- Upstream timeout should produce `success=False`.
- Non-JSON response should produce `success=False`.
- Parsed JSON that misses required contract fields should still go through `normalize_draft`, which fills safe defaults where possible and raises only when adoption validation fails.

## Admin UI

The AI agent management page should show provider choices for domestic adapters and guidance:

- `桂教通 API`: competition/education platform provider.
- `OpenAI兼容本地网关`: local or self-hosted gateway.
- `通义千问`, `DeepSeek`, `智谱GLM`, `豆包`, `百度千帆`, `讯飞星火`, `Kimi`: domestic provider presets.

The form should explain:

- Endpoint/model/key are provider-level config.
- Raw secret values should be stored in backend environment variables when possible.
- Teacher adoption remains required.

## Verification

- Backend tests for provider identifiers in schemas.
- Backend tests for OpenAI-compatible provider request payload, JSON parsing, malformed JSON failure, and missing configuration failure.
- Backend tests for gateway registering the new provider identifiers.
- Frontend route/text checks for domestic provider labels.
- Full release check.

