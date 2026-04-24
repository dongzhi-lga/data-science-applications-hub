from __future__ import annotations

from app.modules.binary_feature_ae.models.ai import (
    ApiBinaryFeatureAiExplainRuleRequest,
    ApiBinaryFeatureAiResponse,
)
from app.modules.binary_feature_ae.service.ai_fallbacks import (
    fallback_explain_focused_rule,
)
from app.modules.binary_feature_ae.service.ai_orchestrator import (
    explain_focused_rule_ai,
)
from app.modules.binary_feature_ae.service.ai_packets import (
    build_explain_focused_rule_packet,
)

build_binary_feature_fallback_explain_response = fallback_explain_focused_rule
build_binary_feature_explain_rule_packet = build_explain_focused_rule_packet

__all__ = [
    "build_binary_feature_explain_rule_packet",
    "build_binary_feature_fallback_explain_response",
    "perform_binary_feature_explain_rule",
]


def perform_binary_feature_explain_rule(
    *,
    params: ApiBinaryFeatureAiExplainRuleRequest,
) -> ApiBinaryFeatureAiResponse:
    return explain_focused_rule_ai(params=params)
