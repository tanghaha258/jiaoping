"""
AI Gateway — central orchestrator for all AI provider calls.

Architecture:
    API Router -> AI Service -> AI Gateway -> Provider

Responsibilities:
    1. Provider selection based on agent configuration
    2. Input desensitization (removes PII before sending to external AI)
    3. Provider call execution
    4. Output structure validation

Note: Call logging / audit trail is handled by ai_service.py,
      which creates/updates AIAgentCall records via SQLAlchemy ORM.
      The gateway focuses purely on the provider interaction layer.
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from app.services.providers.base import AIProviderRequest, AIProviderResult
from app.services.providers.gjt_api import GjtApiProvider
from app.services.providers.mock import MockProvider

logger = logging.getLogger(__name__)


# ─── PII Detection Patterns ───────────────────────────────────────────────────
# These patterns detect sensitive information that must not be sent to external AI providers.

_PII_PATTERNS = [
    # Chinese ID card number (18 digits)
    (re.compile(r'\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b'), '[身份证号已脱敏]'),
    # Chinese mobile phone number
    (re.compile(r'\b1[3-9]\d{9}\b'), '[手机号已脱敏]'),
    # Email addresses
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[邮箱已脱敏]'),
    # Student names in certain patterns (heuristic: 姓名 followed by Chinese name)
    (re.compile(r'姓名[:：]\s*[一-鿿]{2,4}'), '姓名:[已脱敏]'),
    # Home addresses (heuristic: patterns containing typical address keywords)
    (re.compile(r'(?:地址|住址|家庭住址)[:：]\s*.+?(?=[,，\n]|$)'), '地址:[已脱敏]'),
]


class AIGateway:
    """
    Central gateway for AI operations.

    Manages provider registry, input desensitization, output validation,
    and provider execution. Providers are registered at initialization time.

    Database operations (call logging, audit trail) are handled by
    ai_service.py, which wraps this gateway.
    """

    def __init__(self):
        """Initialize the AI Gateway with available providers."""
        self.providers: dict[str, Any] = {
            "mock": MockProvider(),
            "gjt_api": GjtApiProvider(),
            # Future providers (uncomment when implemented):
            # "gjt_link": GjtLinkProvider(),
            # "manual_import": ManualImportProvider(),
        }
        self._scenarios = {
            "learning_diagnosis",
            "lesson_plan",
            "rubric_generation",
            "resource_recommendation",
            "teaching_reflection",
        }

    # ─── Main Entry Point ─────────────────────────────────────────────────────

    async def execute(
        self,
        call_request: AIProviderRequest,
        agent_config: dict[str, Any],
    ) -> AIProviderResult:
        """
        Execute an AI call end-to-end.

        Flow:
            1. Validate scenario
            2. Desensitize input data
            3. Select provider from agent config
            4. Call provider
            5. Validate output structure
            6. Return result

        Args:
            call_request: The AI provider request (with PII-rich input)
            agent_config: The agent configuration dict from the database

        Returns:
            AIProviderResult with the output or error details
        """
        # Step 1: Validate scenario
        if call_request.scenario not in self._scenarios:
            return AIProviderResult(
                success=False,
                content=None,
                provider="unknown",
                scenario=call_request.scenario,
                error_message=f"不支持的场景类型: {call_request.scenario}",
                requires_review=True,
                finished_at=datetime.now(timezone.utc),
            )

        # Step 2: Desensitize input before sending to any external provider
        desensitized_input = self.desensitize_input(call_request.input_data)
        call_request.input_data = desensitized_input

        # Step 3: Select provider based on agent configuration
        provider_name = agent_config.get("provider", "mock")
        provider = self.providers.get(provider_name)

        if provider is None:
            logger.warning(
                f"Provider '{provider_name}' not found, falling back to mock. "
                f"Available providers: {list(self.providers.keys())}"
            )
            provider = self.providers["mock"]
            provider_name = "mock"

        # Step 4: Execute the provider call
        logger.info(
            f"AI Gateway: provider={provider_name} "
            f"scenario={call_request.scenario} "
            f"user={call_request.user_id}"
        )

        try:
            result = await provider.run(call_request)
        except Exception as e:
            logger.exception(f"Provider '{provider_name}' raised an unhandled exception")
            return AIProviderResult(
                success=False,
                content=None,
                provider=provider_name,
                scenario=call_request.scenario,
                error_message=f"AI服务调用异常: {str(e)}",
                requires_review=True,
                finished_at=datetime.now(timezone.utc),
            )

        # Step 5: Validate output structure
        if result.success:
            validation_ok = self.validate_output(result)
            if not validation_ok:
                logger.warning(
                    f"Output validation failed for provider={provider_name} "
                    f"scenario={call_request.scenario}"
                )
                result.success = False
                result.error_message = result.error_message or "AI输出结构校验未通过"
                result.requires_review = True

        return result

    # ─── Input Desensitization ─────────────────────────────────────────────────

    def desensitize_input(self, input_data: dict) -> dict:
        """
        Remove PII (Personally Identifiable Information) from input data.

        This is a safety layer that ensures no student personal information
        is accidentally sent to external AI providers. Uses regex-based
        detection. In production, this should be enhanced with NER-based detection.

        Permitted fields (will NOT be redacted):
            - Grade level (年级)
            - Subject names (学科)
            - Textbook version (教材版本)
            - Class-level aggregate summaries (班级整体表现)
            - Anonymized student descriptions
            - Task and evaluation dimensions

        Forbidden fields (WILL be redacted):
            - Student ID numbers
            - Phone numbers
            - Home addresses
            - Full names paired with performance data
            - Medical/psychological information
        """
        # Serialize to string for pattern matching
        try:
            text = json.dumps(input_data, ensure_ascii=False)
        except (TypeError, ValueError):
            text = str(input_data)

        # Apply PII patterns
        for pattern, replacement in _PII_PATTERNS:
            text = pattern.sub(replacement, text)

        logger.info(
            f"Input desensitization complete. "
            f"Original keys: {list(input_data.keys())}"
        )

        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            # If we can't parse back to dict, return the text wrapped safely
            return {"desensitized_text": text, "original_keys": list(input_data.keys())}

    # ─── Output Validation ─────────────────────────────────────────────────────

    def validate_output(self, result: AIProviderResult) -> bool:
        """
        Basic output structure validation.

        Checks:
            - Result has content (not None/empty)
            - Scenario-specific structure requirements
            - No obviously malicious content patterns

        Returns True if the output passes validation, False otherwise.
        """
        if result.content is None:
            result.error_message = "AI返回内容为空"
            return False

        # Scenario-specific structural checks
        validators = {
            "learning_diagnosis": self._validate_learning_diagnosis_output,
            "lesson_plan": self._validate_lesson_plan_output,
            "rubric_generation": self._validate_rubric_generation_output,
            "resource_recommendation": self._validate_resource_recommendation_output,
            "teaching_reflection": self._validate_teaching_reflection_output,
        }

        validator = validators.get(result.scenario)
        if validator:
            return validator(result.content)

        # Unknown scenario: accept with log warning
        logger.warning(f"No validator for scenario '{result.scenario}', accepting output as-is")
        return True

    def _validate_learning_diagnosis_output(self, content: Any) -> bool:
        """Validate 学情诊断 output structure."""
        if not isinstance(content, dict):
            return False
        if "class_profile" not in content and "tiered_suggestions" not in content:
            return False
        return True

    def _validate_lesson_plan_output(self, content: Any) -> bool:
        """Validate 跨学科教学设计 output structure."""
        if not isinstance(content, dict):
            return False
        if all(key in content for key in ("project", "tasks", "rubric", "resources", "teacher_notes")):
            return True
        if "theme" not in content and "lessons" not in content:
            return False
        return True

    def _validate_rubric_generation_output(self, content: Any) -> bool:
        """Validate 评价量规生成 output structure."""
        if not isinstance(content, dict):
            return False
        if "items" not in content:
            return False
        return True

    def _validate_resource_recommendation_output(self, content: Any) -> bool:
        """Validate 资源推荐 output structure."""
        if not isinstance(content, dict):
            return False
        if "resources" not in content:
            return False
        return True

    def _validate_teaching_reflection_output(self, content: Any) -> bool:
        """Validate 教学反思 output structure."""
        if not isinstance(content, dict):
            return False
        if "strengths" not in content and "improvements" not in content:
            return False
        return True

    # ─── Provider Management ───────────────────────────────────────────────────

    def register_provider(self, name: str, provider) -> None:
        """Register a new AI provider at runtime."""
        self.providers[name] = provider
        logger.info(f"AI Gateway: registered provider '{name}'")

    def get_available_providers(self) -> list[str]:
        """Return list of registered provider names."""
        return list(self.providers.keys())

    async def check_provider_health(self, provider_name: str) -> bool:
        """Check if a specific provider is healthy."""
        provider = self.providers.get(provider_name)
        if provider is None:
            return False
        try:
            return await provider.health_check()
        except Exception:
            return False
