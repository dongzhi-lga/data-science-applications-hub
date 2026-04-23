from __future__ import annotations

import math

import pandas as pd

from app.modules.binary_feature_ae.models.ai import BinaryFeatureAiRuleBaselines


def _to_float(value: object) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(result):
        return 0.0
    return result


def compute_percentile(value: float, series: pd.Series) -> float:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return 0.0
    numeric_value = _to_float(value)
    return float((clean <= numeric_value).sum() / len(clean) * 100.0)


def compute_rule_baselines(
    *,
    visible_df: pd.DataFrame,
    row: pd.Series,
) -> BinaryFeatureAiRuleBaselines:
    impact_score_percentile = compute_percentile(
        _to_float(row.get("impact_score")),
        visible_df["impact_score"],
    )
    hit_count_percentile = compute_percentile(
        _to_float(row.get("hit_count")),
        visible_df["hit_count"],
    )
    claim_count_percentile = compute_percentile(
        _to_float(row.get("claim_count")),
        visible_df["claim_count"],
    )
    claim_amount_percentile = compute_percentile(
        _to_float(row.get("claim_amount")),
        visible_df["claim_amount"],
    )
    ci_width_percentile = compute_percentile(
        _to_float(row.get("ci_width")),
        visible_df["ci_width"],
    )

    return BinaryFeatureAiRuleBaselines(
        impact_score_percentile=impact_score_percentile,
        hit_count_percentile=hit_count_percentile,
        claim_count_percentile=claim_count_percentile,
        claim_amount_percentile=claim_amount_percentile,
        ci_width_percentile=ci_width_percentile,
        low_volume_flag=min(hit_count_percentile, claim_count_percentile) <= 25.0,
        high_uncertainty_flag=ci_width_percentile >= 75.0,
        concentrated_cola_flag=_to_float(row.get("dominant_cola_pct")) >= 50.0,
    )


def compute_divergence_metrics(
    *,
    count_row: pd.Series,
    amount_row: pd.Series,
) -> dict[str, object]:
    count_ae = _to_float(count_row.get("ae_ratio"))
    amount_ae = _to_float(amount_row.get("ae_ratio"))
    count_impact = _to_float(count_row.get("impact_score"))
    amount_impact = _to_float(amount_row.get("impact_score"))

    return {
        "count_significance": str(count_row.get("significance_class", "")),
        "amount_significance": str(amount_row.get("significance_class", "")),
        "significance_differs": str(count_row.get("significance_class", ""))
        != str(amount_row.get("significance_class", "")),
        "count_ae_ratio": count_ae,
        "amount_ae_ratio": amount_ae,
        "ae_ratio_delta": count_ae - amount_ae,
        "count_impact_score": count_impact,
        "amount_impact_score": amount_impact,
        "impact_score_delta": count_impact - amount_impact,
        "count_ci_width": _to_float(count_row.get("ci_width")),
        "amount_ci_width": _to_float(amount_row.get("ci_width")),
        "count_dominant_cola": str(count_row.get("dominant_cola", "")),
        "amount_dominant_cola": str(amount_row.get("dominant_cola", "")),
        "dominant_cola_differs": str(count_row.get("dominant_cola", ""))
        != str(amount_row.get("dominant_cola", "")),
    }
