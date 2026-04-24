from __future__ import annotations

import numpy as np
import pandas as pd

from app.modules.binary_feature_ae.models.ai import (
    ApiBinaryFeatureAiAction,
    ApiBinaryFeatureAiExplainRuleRequest,
    BinaryFeatureAiExplainFocusedRulePacket,
)
from app.modules.binary_feature_ae.service.ai_baselines import (
    compute_rule_baselines,
)
from app.modules.binary_feature_ae.service.view_state import (
    build_binary_feature_view_state,
)

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


def build_explain_focused_rule_packet(
    *,
    params: ApiBinaryFeatureAiExplainRuleRequest,
) -> BinaryFeatureAiExplainFocusedRulePacket:
    view_state = build_binary_feature_view_state(params)
    filtered_sorted_df = view_state.filtered_sorted_df
    target_rows = filtered_sorted_df[
        filtered_sorted_df["row_id"] == params.row_id
    ]
    if target_rows.empty:
        raise ValueError(
            "Selected rule is not visible in the current filtered view"
        )

    focused_row = target_rows.iloc[0]
    baselines = compute_rule_baselines(
        visible_df=filtered_sorted_df,
        row=focused_row,
    )

    return BinaryFeatureAiExplainFocusedRulePacket(
        action_type=ApiBinaryFeatureAiAction.EXPLAIN_FOCUSED_RULE,
        state_fingerprint=view_state.view_fingerprint,
        dataset_name=view_state.dataset_name,
        perspective=_enum_value(params.perspective),
        ci_level=_enum_value(params.ci_level),
        active_filters=_build_active_filters(params),
        kpis=view_state.kpis.model_dump(mode="json"),
        used_reference_context=False,
        reference_snippets=[],
        reference_sources=[],
        focused_row=_serialize_row(focused_row),
        baselines=baselines,
        visible_rule_count=int(len(filtered_sorted_df)),
    )
