from __future__ import annotations

from app.modules.binary_feature_ae.models.ai import (
    ApiBinaryFeatureAiAction,
    ApiBinaryFeatureAiSourceMode,
    BinaryFeatureAiExplainFocusedRulePacket,
    BinaryFeatureAiRuleBaselines,
)
from app.modules.binary_feature_ae.service.ai_fallbacks import (
    fallback_explain_focused_rule,
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
            ci_width_percentile=80.0,
            low_volume_flag=False,
            high_uncertainty_flag=True,
            concentrated_cola_flag=True,
        ),
        visible_rule_count=1,
    )


def test_fallback_explain_focused_rule_returns_valid_schema() -> None:
    response = fallback_explain_focused_rule(_packet())

    assert response.summary_text
    assert response.key_findings
    assert response.validation_notes


def test_fallback_explain_focused_rule_source_mode_is_fallback() -> None:
    response = fallback_explain_focused_rule(_packet())

    assert response.source_mode == ApiBinaryFeatureAiSourceMode.FALLBACK


def test_fallback_explain_focused_rule_action_type_is_explain_focused_rule(
) -> None:
    response = fallback_explain_focused_rule(_packet())

    assert response.action_type == ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE


def test_fallback_explain_focused_rule_includes_evidence_refs() -> None:
    response = fallback_explain_focused_rule(_packet())

    assert len(response.evidence_refs) >= 1


def test_fallback_explain_focused_rule_avoids_forbidden_language() -> None:
    response = fallback_explain_focused_rule(_packet())
    combined = " ".join(
        [
            response.summary_text,
            *response.key_findings,
            *response.caution_flags,
            *response.next_review_steps,
            *(item.reason_label for item in response.evidence_refs),
        ]
    ).lower()

    for phrase in (
        "caused by",
        "proves",
        "root cause",
        "should reprice",
        "should suppress",
        "definitely risky",
        "dangerous",
        "bad risk",
    ):
        assert phrase not in combined
