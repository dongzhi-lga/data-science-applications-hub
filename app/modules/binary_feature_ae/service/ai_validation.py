from __future__ import annotations

import json

from app.modules.binary_feature_ae.models.ai import (
    ApiBinaryFeatureAiAction,
    ApiBinaryFeatureAiReasonType,
    ApiBinaryFeatureAiResponse,
    ApiBinaryFeatureAiSourceMode,
    BinaryFeatureAiExplainFocusedRulePacket,
)

_UNSAFE_PHRASES = [
    "caused by",
    "proves",
    "root cause",
    "should reprice",
    "should suppress",
    "definitely risky",
    "dangerous",
    "bad risk",
]

_LEGACY_REASON_TYPE_MAP = {
    "top_impact": ApiBinaryFeatureAiReasonType.HIGH_MATERIALITY.value,
    "elevated_95": (
        ApiBinaryFeatureAiReasonType.ELEVATED_RELATIVE_TO_EXPECTED.value
    ),
    "elevated_90": (
        ApiBinaryFeatureAiReasonType.ELEVATED_RELATIVE_TO_EXPECTED.value
    ),
    "elevated_80": (
        ApiBinaryFeatureAiReasonType.ELEVATED_RELATIVE_TO_EXPECTED.value
    ),
    "dominant_cola_concentration": (
        ApiBinaryFeatureAiReasonType.VISIBLE_PATTERN.value
    ),
    "below_expected": ApiBinaryFeatureAiReasonType.BELOW_EXPECTED.value,
    "wide_uncertainty": ApiBinaryFeatureAiReasonType.WIDE_UNCERTAINTY.value,
    "count_amount_divergence": (
        ApiBinaryFeatureAiReasonType.COUNT_AMOUNT_DIVERGENCE.value
    ),
    "selected_for_comparison": (
        ApiBinaryFeatureAiReasonType.SELECTED_FOR_COMPARISON.value
    ),
}


def _assert_safe_text(text: str, *, field_name: str) -> None:
    lowered = text.lower()
    for phrase in _UNSAFE_PHRASES:
        if phrase in lowered:
            raise ValueError(
                "LLM output contained forbidden language in "
                f"{field_name}: {phrase}"
            )


def _normalize_reason_types(payload: dict[str, object]) -> dict[str, object]:
    evidence_refs = payload.get("evidence_refs")
    if not isinstance(evidence_refs, list):
        return payload

    normalized_refs: list[object] = []
    for entry in evidence_refs:
        if not isinstance(entry, dict):
            normalized_refs.append(entry)
            continue
        raw_reason_type = entry.get("reason_type")
        normalized_reason_type = _LEGACY_REASON_TYPE_MAP.get(
            str(raw_reason_type),
            str(raw_reason_type),
        )
        normalized_refs.append(
            {
                **entry,
                "reason_type": normalized_reason_type,
            }
        )

    return {
        **payload,
        "evidence_refs": normalized_refs,
    }


def validate_explain_focused_rule_response(
    raw_content: str,
    packet: BinaryFeatureAiExplainFocusedRulePacket,
) -> ApiBinaryFeatureAiResponse:
    parsed = json.loads(raw_content)
    if not isinstance(parsed, dict):
        raise ValueError("LLM output was not a JSON object")

    normalized = _normalize_reason_types(parsed)
    response = ApiBinaryFeatureAiResponse.model_validate(normalized)
    if response.action_type != ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE:
        raise ValueError("LLM returned an unexpected action type")
    if response.state_fingerprint != packet.state_fingerprint:
        raise ValueError("LLM returned the wrong state fingerprint")
    if not response.summary_text.strip():
        raise ValueError("LLM returned an empty summary")

    expected_row_id = str(packet.focused_row.get("row_id", ""))
    expected_rule_label = str(packet.focused_row.get("rule_label", ""))
    for evidence_ref in response.evidence_refs:
        if evidence_ref.row_id != expected_row_id:
            raise ValueError("LLM returned evidence for an unexpected row")
        if evidence_ref.rule_label != expected_rule_label:
            raise ValueError(
                "LLM returned an unexpected rule label in evidence"
            )
        _assert_safe_text(
            evidence_ref.reason_label,
            field_name="evidence_refs.reason_label",
        )

    _assert_safe_text(response.summary_text, field_name="summary_text")
    for field_name, items in (
        ("key_findings", response.key_findings),
        ("caution_flags", response.caution_flags),
        ("next_review_steps", response.next_review_steps),
    ):
        for item in items:
            _assert_safe_text(item, field_name=field_name)

    return response.model_copy(
        update={
            "source_mode": ApiBinaryFeatureAiSourceMode.LLM,
            "used_reference_context": False,
            "reference_sources": [],
            "validation_notes": [],
        }
    )
