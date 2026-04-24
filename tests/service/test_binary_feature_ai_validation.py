from __future__ import annotations

import json

import pytest

from app.modules.binary_feature_ae.models.ai import (
    ApiBinaryFeatureAiAction,
    ApiBinaryFeatureAiReasonType,
    BinaryFeatureAiExplainFocusedRulePacket,
    BinaryFeatureAiRuleBaselines,
)
from app.modules.binary_feature_ae.service.ai_validation import (
    validate_explain_focused_rule_response,
)


def _packet() -> BinaryFeatureAiExplainFocusedRulePacket:
    return BinaryFeatureAiExplainFocusedRulePacket(
        action_type=ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE,
        state_fingerprint="fingerprint-1",
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


def _payload() -> dict[str, object]:
    return {
        "action_type": "explain_focused_rule",
        "state_fingerprint": "fingerprint-1",
        "source_mode": "llm",
        "summary_text": (
            "The selected rule is elevated relative to expected within "
            "the visible set."
        ),
        "key_findings": ["Count A/E is above expected in this filtered view."],
        "caution_flags": ["Claim mix is concentrated in Cancer."],
        "next_review_steps": [
            "Review recent claims contributing to this rule."
        ],
        "evidence_refs": [
            {
                "row_id": "row-1",
                "rule_label": "R1 | Rule One",
                "reason_type": "elevated_relative_to_expected",
                "reason_label": "Elevated 95%",
                "severity": "high",
            }
        ],
        "used_reference_context": False,
        "reference_sources": [],
        "validation_notes": [],
    }


def test_validate_explain_focused_rule_response_valid_response_passes() -> None:
    response = validate_explain_focused_rule_response(
        raw_content=json.dumps(_payload()),
        packet=_packet(),
    )

    assert response.action_type == ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE
    assert response.source_mode == "llm"


def test_validate_explain_focused_rule_response_wrong_fingerprint_fails() -> (
    None
):
    payload = _payload()
    payload["state_fingerprint"] = "wrong"

    with pytest.raises(ValueError, match="wrong state fingerprint"):
        validate_explain_focused_rule_response(
            raw_content=json.dumps(payload),
            packet=_packet(),
        )


def test_validate_explain_focused_rule_response_invalid_row_id_fails() -> None:
    payload = _payload()
    evidence_refs = payload["evidence_refs"]
    assert isinstance(evidence_refs, list)
    evidence_refs[0]["row_id"] = "row-2"  # type: ignore[index]

    with pytest.raises(ValueError, match="unexpected row"):
        validate_explain_focused_rule_response(
            raw_content=json.dumps(payload),
            packet=_packet(),
        )


def test_validate_explain_focused_rule_response_mismatched_rule_label_fails(
) -> None:
    payload = _payload()
    evidence_refs = payload["evidence_refs"]
    assert isinstance(evidence_refs, list)
    evidence_refs[0]["rule_label"] = "R2 | Rule Two"  # type: ignore[index]

    with pytest.raises(ValueError, match="unexpected rule label"):
        validate_explain_focused_rule_response(
            raw_content=json.dumps(payload),
            packet=_packet(),
        )


def test_validate_explain_focused_rule_response_forbidden_phrase_fails(
) -> None:
    payload = _payload()
    payload["summary_text"] = "This proves the rule is dangerous."

    with pytest.raises(ValueError, match="forbidden language"):
        validate_explain_focused_rule_response(
            raw_content=json.dumps(payload),
            packet=_packet(),
        )


def test_validate_explain_focused_rule_response_empty_summary_fails() -> None:
    payload = _payload()
    payload["summary_text"] = "   "

    with pytest.raises(ValueError, match="empty summary"):
        validate_explain_focused_rule_response(
            raw_content=json.dumps(payload),
            packet=_packet(),
        )


def test_validate_explain_focused_rule_response_normalizes_legacy_reason_types(
) -> None:
    payload = _payload()
    evidence_refs = payload["evidence_refs"]
    assert isinstance(evidence_refs, list)
    evidence_refs[0]["reason_type"] = "elevated_95"  # type: ignore[index]

    response = validate_explain_focused_rule_response(
        raw_content=json.dumps(payload),
        packet=_packet(),
    )

    assert (
        response.evidence_refs[0].reason_type
        == ApiBinaryFeatureAiReasonType.ELEVATED_RELATIVE_TO_EXPECTED
    )
