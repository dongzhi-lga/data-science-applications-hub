from __future__ import annotations

import math

from app.modules.binary_feature_ae.models.ai import (
    ApiBinaryFeatureAiAction,
    ApiBinaryFeatureAiEvidenceRef,
    ApiBinaryFeatureAiReasonType,
    ApiBinaryFeatureAiResponse,
    ApiBinaryFeatureAiSeverity,
    ApiBinaryFeatureAiSourceMode,
    BinaryFeatureAiExplainFocusedRulePacket,
    BinaryFeatureAiRuleBaselines,
)

_FALLBACK_VALIDATION_NOTE = (
    "Deterministic fallback used because LLM output was unavailable or invalid."
)


def _to_float(value: object) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(result):
        return 0.0
    return result


def _build_summary_signal(focused_row: dict[str, object]) -> str:
    ci_lower = _to_float(focused_row.get("ci_lower"))
    ci_upper = _to_float(focused_row.get("ci_upper"))
    if ci_lower > 1.0:
        return "elevated relative to expected at the selected confidence level."
    if ci_upper < 1.0:
        return "below expected at the selected confidence level."
    return "an uncertain interval because the confidence interval crosses 1.0."


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
            return "It is material within the visible set on count scale."
        return "It is lower-volume within the visible set on count scale."

    if baselines.claim_amount_percentile >= 75.0:
        return "It is material within the visible set on amount scale."
    return "It is lower-dollar within the visible set on amount scale."


def _build_stability_summary(
    *,
    focused_row: dict[str, object],
    baselines: BinaryFeatureAiRuleBaselines,
) -> str:
    if (
        str(focused_row.get("significance_class", "")) == "Uncertain"
        or baselines.high_uncertainty_flag
    ):
        return "Uncertainty is wide relative to the visible set."
    return "Uncertainty is narrower than the widest visible rules."


def _build_mix_summary(
    *,
    focused_row: dict[str, object],
    baselines: BinaryFeatureAiRuleBaselines,
) -> str:
    dominant_cola = str(
        focused_row.get("dominant_cola", "the largest cause bucket")
    )
    if baselines.concentrated_cola_flag:
        return f"Claim mix is concentrated in {dominant_cola}."
    return f"The largest claim-mix bucket is {dominant_cola}."


def _build_evidence_refs(
    *,
    focused_row: dict[str, object],
    baselines: BinaryFeatureAiRuleBaselines,
) -> list[ApiBinaryFeatureAiEvidenceRef]:
    row_id = str(focused_row.get("row_id", ""))
    rule_label = str(focused_row.get("rule_label", ""))
    refs = [
        ApiBinaryFeatureAiEvidenceRef(
            row_id=row_id,
            rule_label=rule_label,
            reason_type=ApiBinaryFeatureAiReasonType.FOCUSED_RULE,
            reason_label="Selected rule in the current filtered view",
            severity=ApiBinaryFeatureAiSeverity.NEUTRAL,
        )
    ]

    ci_lower = _to_float(focused_row.get("ci_lower"))
    ci_upper = _to_float(focused_row.get("ci_upper"))
    confidence_band = str(focused_row.get("confidence_band", "")).strip()
    if ci_lower > 1.0:
        elevated_label = (
            confidence_band
            or "Elevated relative to expected at the selected confidence level"
        )
        refs.append(
            ApiBinaryFeatureAiEvidenceRef(
                row_id=row_id,
                rule_label=rule_label,
                reason_type=ApiBinaryFeatureAiReasonType.ELEVATED_RELATIVE_TO_EXPECTED,
                reason_label=elevated_label,
                severity=ApiBinaryFeatureAiSeverity.HIGH,
            )
        )
    elif ci_upper < 1.0:
        refs.append(
            ApiBinaryFeatureAiEvidenceRef(
                row_id=row_id,
                rule_label=rule_label,
                reason_type=ApiBinaryFeatureAiReasonType.BELOW_EXPECTED,
                reason_label=confidence_band
                or "Below expected at the selected confidence level",
                severity=ApiBinaryFeatureAiSeverity.MEDIUM,
            )
        )
    else:
        refs.append(
            ApiBinaryFeatureAiEvidenceRef(
                row_id=row_id,
                rule_label=rule_label,
                reason_type=ApiBinaryFeatureAiReasonType.UNCERTAIN_INTERVAL,
                reason_label=(
                    "Confidence interval crosses 1.0 at the selected "
                    "confidence level"
                ),
                severity=ApiBinaryFeatureAiSeverity.MEDIUM,
            )
        )

    if baselines.impact_score_percentile >= 75.0:
        refs.append(
            ApiBinaryFeatureAiEvidenceRef(
                row_id=row_id,
                rule_label=rule_label,
                reason_type=ApiBinaryFeatureAiReasonType.HIGH_MATERIALITY,
                reason_label="Impact score is in the upper visible quartile",
                severity=ApiBinaryFeatureAiSeverity.MEDIUM,
            )
        )

    if baselines.high_uncertainty_flag:
        refs.append(
            ApiBinaryFeatureAiEvidenceRef(
                row_id=row_id,
                rule_label=rule_label,
                reason_type=ApiBinaryFeatureAiReasonType.WIDE_UNCERTAINTY,
                reason_label=(
                    "Confidence interval is wide relative to the visible set"
                ),
                severity=ApiBinaryFeatureAiSeverity.MEDIUM,
            )
        )

    if baselines.concentrated_cola_flag:
        dominant_cola = str(
            focused_row.get("dominant_cola", "the largest cause bucket")
        )
        refs.append(
            ApiBinaryFeatureAiEvidenceRef(
                row_id=row_id,
                rule_label=rule_label,
                reason_type=ApiBinaryFeatureAiReasonType.VISIBLE_PATTERN,
                reason_label=f"Claim mix is concentrated in {dominant_cola}",
                severity=ApiBinaryFeatureAiSeverity.LOW,
            )
        )

    return refs[:5]


def fallback_explain_focused_rule(
    packet: BinaryFeatureAiExplainFocusedRulePacket,
) -> ApiBinaryFeatureAiResponse:
    focused_row = packet.focused_row
    baselines = packet.baselines
    summary_text = " ".join(
        [
            "AI interpretation is unavailable.",
            (
                "Based on the uploaded fields, this rule is shown with "
                f"{_build_summary_signal(focused_row)}"
            ),
            _build_scale_summary(
                perspective=packet.perspective,
                baselines=baselines,
            ),
            _build_stability_summary(
                focused_row=focused_row,
                baselines=baselines,
            ),
            _build_mix_summary(
                focused_row=focused_row,
                baselines=baselines,
            ),
        ]
    )

    key_findings = [
        (
            f"{focused_row['confidence_band']} with {packet.perspective} A/E "
            f"{_to_float(focused_row['ae_ratio']):.4f} and CI "
            f"[{_to_float(focused_row['ci_lower']):.4f}, "
            f"{_to_float(focused_row['ci_upper']):.4f}]."
        ),
        (
            f"Impact score is around the "
            f"{baselines.impact_score_percentile:.0f}th percentile of "
            "visible rules."
        ),
        (
            f"Hit count is around the {baselines.hit_count_percentile:.0f}th "
            "percentile and claim count is around the "
            f"{baselines.claim_count_percentile:.0f}th percentile."
        ),
        (
            f"Largest claim-mix bucket is {focused_row['dominant_cola']} at "
            f"{_to_float(focused_row['dominant_cola_pct']):.1f}%."
        ),
    ]

    caution_flags: list[str] = []
    if baselines.low_volume_flag:
        caution_flags.append(
            "Volume is light relative to the visible rules, so small "
            "changes may move the ratio materially."
        )
    if (
        str(focused_row.get("significance_class", "")) == "Uncertain"
        or baselines.high_uncertainty_flag
    ):
        caution_flags.append(
            "The interval is wide enough that this signal should be "
            "treated as uncertain."
        )
    if baselines.concentrated_cola_flag:
        caution_flags.append(
            f"The signal is concentrated in {focused_row['dominant_cola']}, "
            "so one claim family may represent much of the visible pattern."
        )

    significance_class = str(focused_row.get("significance_class", ""))
    if significance_class == "Elevated":
        next_review_steps = [
            "Review recent claims tied to this rule and compare them "
            "with nearby rules in the current filtered view.",
        ]
    elif significance_class == "Below Expected":
        next_review_steps = [
            "Check whether the below-expected result stays similar "
            "across adjacent periods or nearby filters.",
        ]
    else:
        next_review_steps = [
            "Keep this rule on a watchlist and revisit after more "
            "volume or a broader comparison set is available.",
        ]

    next_review_steps.append(
        "Compare count and amount perspectives to see whether "
        "frequency and severity tell a similar story."
    )
    next_review_steps.append(
        "Use the visible table and detail cards to confirm whether "
        "nearby rules show a similar pattern."
    )

    return ApiBinaryFeatureAiResponse(
        action_type=ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE,
        state_fingerprint=packet.state_fingerprint,
        source_mode=ApiBinaryFeatureAiSourceMode.FALLBACK,
        summary_text=summary_text,
        key_findings=key_findings,
        caution_flags=caution_flags,
        next_review_steps=next_review_steps,
        evidence_refs=_build_evidence_refs(
            focused_row=focused_row,
            baselines=baselines,
        ),
        used_reference_context=False,
        reference_sources=[],
        validation_notes=[_FALLBACK_VALIDATION_NOTE],
    )
