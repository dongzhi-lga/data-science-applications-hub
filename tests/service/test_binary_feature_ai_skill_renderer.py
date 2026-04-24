from __future__ import annotations

import pytest

from app.modules.binary_feature_ae.models.ai import (
    ApiBinaryFeatureAiAction,
    BinaryFeatureAiExplainFocusedRulePacket,
    BinaryFeatureAiRuleBaselines,
    BinaryFeatureAiSkillDefinition,
)
from app.modules.binary_feature_ae.service.ai_skill_loader import load_skill
from app.modules.binary_feature_ae.service.ai_skill_renderer import (
    render_skill_prompt,
)


def _packet() -> BinaryFeatureAiExplainFocusedRulePacket:
    return BinaryFeatureAiExplainFocusedRulePacket(
        action_type=ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE,
        state_fingerprint="abc123",
        dataset_name="demo",
        perspective="count",
        ci_level="95",
        active_filters={"categories": ["Cancer"]},
        kpis={"visible_rule_count": 1},
        used_reference_context=False,
        reference_snippets=[],
        reference_sources=[],
        focused_row={
            "row_id": "row-1",
            "rule_label": "R1 | Rule One",
            "confidence_band": "Elevated 95%",
            "ae_ratio": 1.4,
            "ci_lower": 1.2,
            "ci_upper": 1.6,
            "significance_class": "Elevated",
            "dominant_cola": "Cancer",
            "dominant_cola_pct": 60.0,
        },
        baselines=BinaryFeatureAiRuleBaselines(
            impact_score_percentile=90.0,
            hit_count_percentile=80.0,
            claim_count_percentile=75.0,
            claim_amount_percentile=70.0,
            ci_width_percentile=60.0,
            low_volume_flag=False,
            high_uncertainty_flag=False,
            concentrated_cola_flag=True,
        ),
        visible_rule_count=1,
    )


def test_render_skill_prompt_injects_context_packet() -> None:
    skill = load_skill("explain_focused_rule")

    rendered = render_skill_prompt(skill=skill, packet=_packet())

    assert '"state_fingerprint":"abc123"' in rendered.system_prompt
    assert "{{ context_packet }}" not in rendered.system_prompt


def test_render_skill_prompt_missing_placeholder_fails_safely() -> None:
    skill = BinaryFeatureAiSkillDefinition(
        name="explain_focused_rule",
        action_type=ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE,
        version="v1",
        model_profile="standard_interpretation",
        temperature=0.1,
        response_schema="rule_explanation",
        body="# TASK\nNo placeholder here.\n",
    )

    with pytest.raises(
        ValueError, match="missing the context_packet placeholder"
    ):
        render_skill_prompt(skill=skill, packet=_packet())


def test_render_skill_prompt_contains_immutable_rules() -> None:
    skill = load_skill("explain_focused_rule")

    rendered = render_skill_prompt(skill=skill, packet=_packet())

    assert "Do not calculate actuarial metrics." in rendered.system_prompt
    assert "Do not claim causality." in rendered.system_prompt
