from __future__ import annotations

import json
import logging

import numpy as np
import pandas as pd

from app.core.llm import get_llm_config, request_chat_completion_content
from app.modules.binary_feature_ae.models.ai import (
    ApiBinaryFeatureAiAction,
    ApiBinaryFeatureAiEvidenceRef,
    ApiBinaryFeatureAiExplainRuleRequest,
    ApiBinaryFeatureAiReasonType,
    ApiBinaryFeatureAiResponse,
    ApiBinaryFeatureAiSeverity,
    ApiBinaryFeatureAiSourceMode,
    BinaryFeatureAiExplainRulePacket,
    BinaryFeatureAiRuleBaselines,
)
from app.modules.binary_feature_ae.service.ai_baselines import compute_rule_baselines
from app.modules.binary_feature_ae.service.view_state import build_binary_feature_view_state

logger = logging.getLogger(__name__)

_PACKET_ROW_FIELDS = [
    "row_id",
    "rule",
    "RuleName",
    "rule_label",
    "first_date",
    "category",
    "hit_count",
    "hit_rate",
    "claim_count",
    "claim_amount",
    "mec_sum",
    "men_sum",
    "ae_ratio",
    "ci_lower",
    "ci_upper",
    "ci_width",
    "impact_score",
    "significance_class",
    "dominant_cola",
    "dominant_cola_pct",
    "confidence_band",
]


def _to_float(value: object) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    if np.isnan(result):
        return 0.0
    return result


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


def _serialize_value(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, np.generic):
        return value.item()
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _serialize_row(row: pd.Series) -> dict[str, object]:
    serialized: dict[str, object] = {}
    for field in _PACKET_ROW_FIELDS:
        serialized[field] = _serialize_value(row.get(field))
    return serialized


def _build_active_filters(
    params: ApiBinaryFeatureAiExplainRuleRequest,
) -> dict[str, object]:
    return {
        "categories": sorted(params.categories),
        "significance_values": sorted(
            _enum_value(value) for value in params.significance_values
        ),
        "search_text": (params.search_text or "").strip() or None,
        "min_hit_count": 0.0
        if params.min_hit_count is None
        else float(params.min_hit_count),
        "min_claim_count": 0.0
        if params.min_claim_count is None
        else float(params.min_claim_count),
    }


def _build_summary_signal(rule_row: dict[str, object]) -> str:
    ci_lower = _to_float(rule_row.get("ci_lower"))
    ci_upper = _to_float(rule_row.get("ci_upper"))
    if ci_lower > 1.0:
        return "Statistically elevated above expected at the selected confidence level."
    if ci_upper < 1.0:
        return "Statistically below expected at the selected confidence level."
    return "Not clearly different from expected because the interval crosses 1.0."


def _build_scale_summary(
    *,
    perspective: str,
    baselines: BinaryFeatureAiRuleBaselines,
) -> str:
    if perspective == "count":
        if (
            baselines.hit_count_percentile >= 75.0
            or baselines.claim_count_percentile >= 75.0
        ):
            return "Material count scale relative to the visible rules."
        return "Lower-volume count rule relative to the visible rules."

    if baselines.claim_amount_percentile >= 75.0:
        return "Material amount scale relative to the visible rules."
    return "Lower-dollar rule relative to the visible rules."


def _build_stability_summary(
    *,
    rule_row: dict[str, object],
    baselines: BinaryFeatureAiRuleBaselines,
) -> str:
    if (
        str(rule_row.get("significance_class", "")) == "Uncertain"
        or baselines.high_uncertainty_flag
    ):
        return "Uncertainty is relatively wide within the current view."
    return "Confidence interval is tighter than the highest-uncertainty rules."


def _build_mix_summary(
    *,
    perspective: str,
    rule_row: dict[str, object],
    baselines: BinaryFeatureAiRuleBaselines,
) -> str:
    dominant_cola = str(rule_row.get("dominant_cola", "this cause bucket"))
    if baselines.concentrated_cola_flag:
        return (
            f"{perspective.title()} claim mix is concentrated in {dominant_cola}."
        )
    return (
        f"{perspective.title()} claim mix is more balanced, with {dominant_cola} "
        "as the largest component."
    )


def _band_reason_type(rule_row: dict[str, object]) -> ApiBinaryFeatureAiReasonType:
    confidence_band = str(rule_row.get("confidence_band", ""))
    if confidence_band.startswith("Elevated 95"):
        return ApiBinaryFeatureAiReasonType.ELEVATED_95
    if confidence_band.startswith("Elevated 90"):
        return ApiBinaryFeatureAiReasonType.ELEVATED_90
    if confidence_band.startswith("Elevated 80"):
        return ApiBinaryFeatureAiReasonType.ELEVATED_80
    return ApiBinaryFeatureAiReasonType.BELOW_EXPECTED


def _build_evidence_refs(
    *,
    rule_row: dict[str, object],
    baselines: BinaryFeatureAiRuleBaselines,
) -> list[ApiBinaryFeatureAiEvidenceRef]:
    row_id = str(rule_row.get("row_id", ""))
    rule_label = str(rule_row.get("rule_label", ""))
    refs: list[ApiBinaryFeatureAiEvidenceRef] = []

    significance_class = str(rule_row.get("significance_class", ""))
    if significance_class in {"Elevated", "Below Expected"}:
        reason_type = _band_reason_type(rule_row)
        reason_label = (
            str(rule_row.get("confidence_band", ""))
            or f"{significance_class} at the selected confidence level"
        )
        refs.append(
            ApiBinaryFeatureAiEvidenceRef(
                row_id=row_id,
                rule_label=rule_label,
                reason_type=reason_type,
                reason_label=reason_label,
                severity=ApiBinaryFeatureAiSeverity.HIGH
                if significance_class == "Elevated"
                else ApiBinaryFeatureAiSeverity.MEDIUM,
            )
        )

    if baselines.impact_score_percentile >= 75.0:
        refs.append(
            ApiBinaryFeatureAiEvidenceRef(
                row_id=row_id,
                rule_label=rule_label,
                reason_type=ApiBinaryFeatureAiReasonType.TOP_IMPACT,
                reason_label="Impact score ranks in the upper visible quartile",
                severity=ApiBinaryFeatureAiSeverity.MEDIUM,
            )
        )

    if baselines.high_uncertainty_flag:
        refs.append(
            ApiBinaryFeatureAiEvidenceRef(
                row_id=row_id,
                rule_label=rule_label,
                reason_type=ApiBinaryFeatureAiReasonType.WIDE_UNCERTAINTY,
                reason_label="Confidence interval is wide relative to the view",
                severity=ApiBinaryFeatureAiSeverity.MEDIUM,
            )
        )

    if baselines.concentrated_cola_flag:
        dominant_cola = str(rule_row.get("dominant_cola", "one cause bucket"))
        refs.append(
            ApiBinaryFeatureAiEvidenceRef(
                row_id=row_id,
                rule_label=rule_label,
                reason_type=ApiBinaryFeatureAiReasonType.DOMINANT_COLA_CONCENTRATION,
                reason_label=f"Claim mix is concentrated in {dominant_cola}",
                severity=ApiBinaryFeatureAiSeverity.LOW,
            )
        )

    return refs[:4]


def build_binary_feature_explain_rule_packet(
    *,
    params: ApiBinaryFeatureAiExplainRuleRequest,
) -> BinaryFeatureAiExplainRulePacket:
    view_state = build_binary_feature_view_state(params)
    filtered_sorted_df = view_state.filtered_sorted_df
    target_rows = filtered_sorted_df[filtered_sorted_df["row_id"] == params.row_id]
    if target_rows.empty:
        raise ValueError("Selected rule is not visible in the current filtered view")

    target_row = target_rows.iloc[0]
    baselines = compute_rule_baselines(
        visible_df=filtered_sorted_df,
        row=target_row,
    )

    return BinaryFeatureAiExplainRulePacket(
        action_type=ApiBinaryFeatureAiAction.EXPLAIN_RULE,
        state_fingerprint=view_state.view_fingerprint,
        dataset_name=view_state.dataset_name,
        perspective=_enum_value(params.perspective),
        ci_level=_enum_value(params.ci_level),
        active_filters=_build_active_filters(params),
        kpis=view_state.kpis.model_dump(mode="json"),
        used_reference_context=False,
        reference_snippets=[],
        reference_sources=[],
        rule_row=_serialize_row(target_row),
        baselines=baselines,
        visible_rule_count=int(len(filtered_sorted_df)),
    )


def build_binary_feature_fallback_explain_response(
    *,
    packet: BinaryFeatureAiExplainRulePacket,
) -> ApiBinaryFeatureAiResponse:
    rule_row = packet.rule_row
    baselines = packet.baselines
    summary_text = " ".join(
        [
            _build_summary_signal(rule_row),
            _build_scale_summary(
                perspective=packet.perspective,
                baselines=baselines,
            ),
            _build_stability_summary(rule_row=rule_row, baselines=baselines),
            _build_mix_summary(
                perspective=packet.perspective,
                rule_row=rule_row,
                baselines=baselines,
            ),
        ]
    )

    key_findings = [
        (
            f"{rule_row['confidence_band']} with {packet.perspective} A/E "
            f"{_to_float(rule_row['ae_ratio']):.4f} and CI "
            f"[{_to_float(rule_row['ci_lower']):.4f}, "
            f"{_to_float(rule_row['ci_upper']):.4f}]."
        ),
        (
            f"Impact score is around the "
            f"{baselines.impact_score_percentile:.0f}th percentile of visible rules."
        ),
        (
            f"Hit count is around the {baselines.hit_count_percentile:.0f}th "
            "percentile and claim count is around the "
            f"{baselines.claim_count_percentile:.0f}th percentile."
        ),
        (
            f"Largest claim-mix bucket is {rule_row['dominant_cola']} at "
            f"{_to_float(rule_row['dominant_cola_pct']):.1f}%."
        ),
    ]

    caution_flags: list[str] = []
    if baselines.low_volume_flag:
        caution_flags.append(
            "Volume is light relative to the visible rules, so small changes may "
            "move the ratio materially."
        )
    if (
        str(rule_row.get("significance_class", "")) == "Uncertain"
        or baselines.high_uncertainty_flag
    ):
        caution_flags.append(
            "The interval is wide enough that the current signal should be "
            "treated as provisional."
        )
    if baselines.concentrated_cola_flag:
        caution_flags.append(
            f"The signal is concentrated in {rule_row['dominant_cola']}, so one "
            "claim family may be driving the result."
        )

    next_review_steps: list[str] = []
    significance_class = str(rule_row.get("significance_class", ""))
    if significance_class == "Elevated":
        next_review_steps.append(
            f"Review recent claims behind {rule_row['rule']} with emphasis on "
            f"{rule_row['dominant_cola']} drivers."
        )
    elif significance_class == "Below Expected":
        next_review_steps.append(
            "Check whether the lower-than-expected result stays consistent across "
            "adjacent periods or broader filters."
        )
    else:
        next_review_steps.append(
            "Keep the rule on watchlist and revisit after more volume or a wider "
            "comparison set is available."
        )

    if packet.perspective == "count":
        next_review_steps.append(
            "Compare count and amount perspectives before escalating the rule."
        )
    else:
        next_review_steps.append(
            "Confirm whether dollar severity remains elevated after looking at "
            "count-side frequency."
        )

    next_review_steps.append(
        "Use the detailed cards and compare table to validate whether nearby rules "
        "show the same pattern."
    )

    return ApiBinaryFeatureAiResponse(
        action_type=ApiBinaryFeatureAiAction.EXPLAIN_RULE,
        state_fingerprint=packet.state_fingerprint,
        source_mode=ApiBinaryFeatureAiSourceMode.FALLBACK,
        summary_text=summary_text,
        key_findings=key_findings,
        caution_flags=caution_flags,
        next_review_steps=next_review_steps,
        evidence_refs=_build_evidence_refs(
            rule_row=rule_row,
            baselines=baselines,
        ),
        used_reference_context=False,
        reference_sources=[],
    )


def _build_system_prompt(*, prompt_version: str) -> str:
    return (
        "You are a careful actuarial triage copilot for Binary Feature Mortality "
        f"A/E review. Prompt version: {prompt_version}. Explain one selected rule "
        "using only the provided packet. Do not claim causality, external facts, "
        "or remediation certainty. Prefer caution over drama.\n\n"
        "Return JSON only with this schema:\n"
        "{"
        '"action_type":"explain_rule",'
        '"state_fingerprint":"string",'
        '"source_mode":"llm",'
        '"summary_text":"string",'
        '"key_findings":["string"],'
        '"caution_flags":["string"],'
        '"next_review_steps":["string"],'
        '"evidence_refs":[{'
        '"row_id":"string",'
        '"rule_label":"string",'
        '"reason_type":"top_impact|elevated_95|elevated_90|elevated_80|'
        'below_expected|wide_uncertainty|dominant_cola_concentration|'
        'count_amount_divergence|selected_for_comparison",'
        '"reason_label":"string",'
        '"severity":"high|medium|low|neutral"'
        "}],"
        '"used_reference_context":false,'
        '"reference_sources":[]'
        "}"
    )


def _build_user_prompt(packet: BinaryFeatureAiExplainRulePacket) -> str:
    return (
        "Explain the selected rule for an analyst reviewing the current filtered "
        "Binary Feature view.\n"
        "Stay grounded in the packet and keep each bullet short.\n\n"
        "Packet:\n"
        f"{json.dumps(packet.model_dump(mode='json'), indent=2, sort_keys=True)}"
    )


def _parse_llm_response(
    *,
    raw_content: str,
    packet: BinaryFeatureAiExplainRulePacket,
) -> ApiBinaryFeatureAiResponse:
    parsed = json.loads(raw_content)
    response = ApiBinaryFeatureAiResponse.model_validate(parsed)
    if response.action_type != ApiBinaryFeatureAiAction.EXPLAIN_RULE:
        raise ValueError("LLM returned an unexpected action type")
    if response.state_fingerprint != packet.state_fingerprint:
        raise ValueError("LLM returned the wrong state fingerprint")
    if not response.summary_text.strip():
        raise ValueError("LLM returned an empty summary")

    row_id = str(packet.rule_row.get("row_id", ""))
    for evidence_ref in response.evidence_refs:
        if evidence_ref.row_id != row_id:
            raise ValueError("LLM returned evidence for an unexpected row")

    return response.model_copy(
        update={
            "source_mode": ApiBinaryFeatureAiSourceMode.LLM,
            "used_reference_context": False,
            "reference_sources": [],
        }
    )


def perform_binary_feature_explain_rule(
    *,
    params: ApiBinaryFeatureAiExplainRuleRequest,
) -> ApiBinaryFeatureAiResponse:
    packet = build_binary_feature_explain_rule_packet(params=params)
    fallback = build_binary_feature_fallback_explain_response(packet=packet)

    llm_config = get_llm_config()
    if not llm_config.is_configured:
        return fallback

    try:
        raw_content = request_chat_completion_content(
            system_prompt=_build_system_prompt(
                prompt_version=llm_config.prompt_version
            ),
            user_prompt=_build_user_prompt(packet),
            config=llm_config,
        )
        return _parse_llm_response(raw_content=raw_content, packet=packet)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Falling back to deterministic explain_rule output for row '%s': %s",
            params.row_id,
            exc,
        )
        return fallback
