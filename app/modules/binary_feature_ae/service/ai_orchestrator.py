from __future__ import annotations

import logging

from app.core.llm import get_llm_config, request_chat_completion_content
from app.modules.binary_feature_ae.models.ai import (
    ApiBinaryFeatureAiAction,
    ApiBinaryFeatureAiExplainRuleRequest,
    ApiBinaryFeatureAiResponse,
)
from app.modules.binary_feature_ae.service.ai_fallbacks import (
    fallback_explain_focused_rule,
)
from app.modules.binary_feature_ae.service.ai_packets import (
    build_explain_focused_rule_packet,
)
from app.modules.binary_feature_ae.service.ai_skill_loader import load_skill
from app.modules.binary_feature_ae.service.ai_skill_renderer import (
    render_skill_prompt,
)
from app.modules.binary_feature_ae.service.ai_validation import (
    validate_explain_focused_rule_response,
)

logger = logging.getLogger(__name__)


def explain_focused_rule_ai(
    *,
    params: ApiBinaryFeatureAiExplainRuleRequest,
) -> ApiBinaryFeatureAiResponse:
    packet = build_explain_focused_rule_packet(params=params)
    fallback = fallback_explain_focused_rule(packet)

    llm_config = get_llm_config()
    if not llm_config.is_configured:
        return fallback

    try:
        skill = load_skill(ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE)
        prompt = render_skill_prompt(skill=skill, packet=packet)
        raw_content = request_chat_completion_content(
            system_prompt=prompt.system_prompt,
            user_prompt=prompt.user_prompt,
            config=llm_config,
        )
        return validate_explain_focused_rule_response(
            raw_content=raw_content,
            packet=packet,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Falling back to deterministic explain_focused_rule "
            "output for row '%s': %s",
            params.row_id,
            exc,
        )
        return fallback
