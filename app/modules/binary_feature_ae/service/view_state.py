from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol

import pandas as pd

from app.modules.binary_feature_ae.models.triage import ApiBinaryFeatureKpis
from app.modules.binary_feature_ae.service.binary_calc import (
    apply_filters,
    build_binary_feature_kpis,
    load_prepared_binary_feature_df_from_config,
    project_binary_feature_perspective,
    sort_binary_feature_rows,
)


class BinaryFeatureViewParams(Protocol):
    config_id: str
    perspective: object
    ci_level: object
    categories: list[str]
    significance_values: list[object]
    search_text: str | None
    min_hit_count: float | None
    min_claim_count: float | None


@dataclass(frozen=True)
class BinaryFeatureViewState:
    dataset_name: str
    base_df: pd.DataFrame
    projected_df: pd.DataFrame
    filtered_sorted_df: pd.DataFrame
    available_categories: list[str]
    view_fingerprint: str
    kpis: ApiBinaryFeatureKpis


def _enum_value(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


def _normalize_search_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def _normalize_float(value: float | None) -> float:
    return 0.0 if value is None else float(value)


def _normalize_significance_values(values: list[object]) -> list[str]:
    return sorted(_enum_value(value) for value in values)


def build_view_fingerprint(
    *,
    config_id: str,
    perspective: str,
    ci_level: str,
    categories: list[str],
    significance_values: list[str],
    search_text: str | None,
    min_hit_count: float | None,
    min_claim_count: float | None,
    visible_row_ids: list[str],
) -> str:
    payload = {
        "config_id": config_id,
        "perspective": perspective,
        "ci_level": ci_level,
        "categories": sorted(categories),
        "significance_values": sorted(significance_values),
        "search_text": _normalize_search_text(search_text),
        "min_hit_count": _normalize_float(min_hit_count),
        "min_claim_count": _normalize_float(min_claim_count),
        "visible_row_ids": visible_row_ids,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()[:16]


def build_binary_feature_view_state(
    params: BinaryFeatureViewParams,
) -> BinaryFeatureViewState:
    dataset_name, base_df = load_prepared_binary_feature_df_from_config(
        config_id=params.config_id
    )
    available_categories = sorted(
        base_df["category"].dropna().unique().tolist()
    )

    perspective = _enum_value(params.perspective)
    ci_level = _enum_value(params.ci_level)
    significance_values = [
        _enum_value(value) for value in params.significance_values
    ]

    projected_df = project_binary_feature_perspective(
        base_df,
        perspective=perspective,
        ci_level=ci_level,
    )
    filtered_df = apply_filters(
        projected_df,
        categories=params.categories,
        significance_values=significance_values,
        search_text=params.search_text,
        min_hit_count=params.min_hit_count,
        min_claim_count=params.min_claim_count,
    )
    filtered_sorted_df = sort_binary_feature_rows(
        filtered_df,
        perspective=perspective,
    )
    filtered_sorted_df["confidence_band"] = filtered_sorted_df[
        "confidence_band"
    ].astype(str)

    visible_row_ids = [
        str(row_id) for row_id in filtered_sorted_df["row_id"].tolist()
    ]
    view_fingerprint = build_view_fingerprint(
        config_id=params.config_id,
        perspective=perspective,
        ci_level=ci_level,
        categories=params.categories,
        significance_values=_normalize_significance_values(
            params.significance_values
        ),
        search_text=params.search_text,
        min_hit_count=params.min_hit_count,
        min_claim_count=params.min_claim_count,
        visible_row_ids=visible_row_ids,
    )

    return BinaryFeatureViewState(
        dataset_name=dataset_name,
        base_df=base_df,
        projected_df=projected_df,
        filtered_sorted_df=filtered_sorted_df,
        available_categories=available_categories,
        view_fingerprint=view_fingerprint,
        kpis=build_binary_feature_kpis(filtered_sorted_df),
    )
