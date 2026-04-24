from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.models.dataset_config import get_binary_feature_module_config
from app.core.service.dataframe_loader import read_dataframe_from_path
from app.core.service.dataset_config import get_dataset_config_with_file
from app.modules.binary_feature_ae.models.triage import (
    ApiBinaryFeatureCalculateRequest,
    ApiBinaryFeatureCalculateResponse,
    ApiBinaryFeatureKpis,
    ApiBinaryFeaturePerspective,
    ApiBinaryFeatureRow,
)

SHARED_FIELD_LABELS: dict[str, str] = {
    "rule": "rule",
    "RuleName": "RuleName",
    "first_date": "first_date",
    "category": "category",
    "hit_count": "hit_count",
    "hit_rate": "hit_rate",
    "claim_count": "claim_count",
    "claim_amount": "claim_amount",
    "men_sum": "men_sum",
    "mec_sum": "mec_sum",
}

COLA_DEFINITIONS: list[tuple[str, str]] = [
    ("cola_cancer_pct", "Cancer"),
    ("cola_heart_pct", "Heart"),
    ("cola_nervous_system_pct", "Nervous System"),
    ("cola_non_natural_pct", "Non-natural"),
    ("cola_other_medical_pct", "Other Medical"),
    ("cola_respiratory_pct", "Respiratory"),
    ("cola_others_pct", "Others"),
]

CI_LEVELS = ("95", "90", "80")

PERSPECTIVE_CONFIGS: dict[str, dict[str, object]] = {
    ApiBinaryFeaturePerspective.COUNT.value: {
        "ae_ratio_col": "ae_ratio_count",
        "ci_cols": {
            "95": ("ci_lower_95_count", "ci_upper_95_count"),
            "90": ("ci_lower_90_count", "ci_upper_90_count"),
            "80": ("ci_lower_80_count", "ci_upper_80_count"),
        },
        "cola_cols": [f"{base}_count" for base, _ in COLA_DEFINITIONS],
        "dominant_labels": {
            f"{base}_count": label for base, label in COLA_DEFINITIONS
        },
        "scale_col": "hit_count",
        "sort_cols": ["claim_count", "hit_count"],
    },
    ApiBinaryFeaturePerspective.AMOUNT.value: {
        "ae_ratio_col": "ae_ratio_amount",
        "ci_cols": {
            "95": ("ci_lower_95_amount", "ci_upper_95_amount"),
            "90": ("ci_lower_90_amount", "ci_upper_90_amount"),
            "80": ("ci_lower_80_amount", "ci_upper_80_amount"),
        },
        "cola_cols": [f"{base}_amount" for base, _ in COLA_DEFINITIONS],
        "dominant_labels": {
            f"{base}_amount": label for base, label in COLA_DEFINITIONS
        },
        "scale_col": "claim_amount",
        "sort_cols": ["claim_amount", "claim_count"],
    },
}

CONFIDENCE_BAND_ORDER = [
    "Elevated 95%",
    "Elevated 90%",
    "Elevated 80%",
    "Uncertain",
    "Below Expected 80%",
    "Below Expected 90%",
    "Below Expected 95%",
]

REQUIRED_COLS = list(SHARED_FIELD_LABELS)
for perspective in PERSPECTIVE_CONFIGS.values():
    REQUIRED_COLS.append(str(perspective["ae_ratio_col"]))
    ci_cols = perspective["ci_cols"]
    for lo_col, hi_col in ci_cols.values():
        REQUIRED_COLS.extend([lo_col, hi_col])
    REQUIRED_COLS.extend(perspective["cola_cols"])


def _rule_key_for(rule: str, first_date: str) -> str:
    return f"{len(rule)}:{rule}|{len(first_date)}:{first_date}"


def _build_required_label_map() -> dict[str, str]:
    labels = dict(SHARED_FIELD_LABELS)
    for base, _ in COLA_DEFINITIONS:
        label_base = base.replace(
            "cola_non_natural_pct", "cola_non-natural_pct"
        )
        labels[f"{base}_count"] = f"{label_base}_count"
        labels[f"{base}_amount"] = f"{label_base}_amount"
    return labels


REQUIRED_LABELS = _build_required_label_map()


def _flatten_numeric_cols() -> list[str]:
    numeric_cols = [
        "hit_count",
        "hit_rate",
        "claim_count",
        "claim_amount",
        "men_sum",
        "mec_sum",
    ]
    for perspective in PERSPECTIVE_CONFIGS.values():
        numeric_cols.append(str(perspective["ae_ratio_col"]))
        ci_cols = perspective["ci_cols"]
        for lo_col, hi_col in ci_cols.values():
            numeric_cols.extend([lo_col, hi_col])
        numeric_cols.extend(perspective["cola_cols"])
    return numeric_cols


NUMERIC_COLS = _flatten_numeric_cols()


def _project_perspective(
    df: pd.DataFrame,
    *,
    perspective: str,
    ci_level: str,
) -> pd.DataFrame:
    config = PERSPECTIVE_CONFIGS[perspective]
    ci_cols: dict[str, tuple[str, str]] = config["ci_cols"]  # type: ignore[assignment]
    dff = df.copy()

    dff["ae_ratio"] = dff[str(config["ae_ratio_col"])]
    for level, (lo_col, hi_col) in ci_cols.items():
        dff[f"ci_lower_{level}"] = dff[lo_col]
        dff[f"ci_upper_{level}"] = dff[hi_col]
        dff[f"significance_class_{level}"] = dff[
            f"significance_class_{level}_{perspective}"
        ]

    active_ci_lower, active_ci_upper = ci_cols[ci_level]
    dff["significance_class"] = dff[f"significance_class_{ci_level}"]
    dff["ci_lower"] = dff[active_ci_lower]
    dff["ci_upper"] = dff[active_ci_upper]
    dff["ae_gap"] = dff[f"ae_gap_{perspective}"]
    dff["abs_ae_gap"] = dff[f"abs_ae_gap_{perspective}"]
    dff["ci_width"] = dff[f"ci_width_{perspective}"]
    dff["impact_score"] = dff[f"impact_score_{perspective}"]
    dff["dominant_cola"] = dff[f"dominant_cola_{perspective}"]
    dff["dominant_cola_pct"] = dff[f"dominant_cola_pct_{perspective}"]
    dff["confidence_band"] = dff[f"confidence_band_{perspective}"]

    for base, _label in COLA_DEFINITIONS:
        family_col = f"{base}_{perspective}"
        dff[base] = dff[family_col]
        dff[f"{base}_display"] = dff[f"{family_col}_display"]

    return dff


def _sort_rows(df: pd.DataFrame, *, perspective: str) -> pd.DataFrame:
    sort_cols = ["impact_score", *PERSPECTIVE_CONFIGS[perspective]["sort_cols"]]
    ascending = [False] * len(sort_cols)
    return df.sort_values(sort_cols, ascending=ascending).reset_index(drop=True)


def project_binary_feature_perspective(
    df: pd.DataFrame,
    *,
    perspective: str,
    ci_level: str,
) -> pd.DataFrame:
    return _project_perspective(
        df,
        perspective=perspective,
        ci_level=ci_level,
    )


def sort_binary_feature_rows(
    df: pd.DataFrame, *, perspective: str
) -> pd.DataFrame:
    return _sort_rows(df, perspective=perspective)


def prepare_rule_df(df: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in REQUIRED_COLS if column not in df.columns]
    if missing:
        missing_labels = [REQUIRED_LABELS.get(name, name) for name in missing]
        raise ValueError(f"Missing required columns: {missing_labels}")

    dff = df.copy().reset_index(drop=True)
    dff["rule"] = dff["rule"].fillna("").astype(str)
    dff["RuleName"] = dff["RuleName"].fillna("").astype(str)
    dff["first_date"] = dff["first_date"].fillna("").astype(str)
    dff["category"] = dff["category"].fillna("Uncategorized").astype(str)
    dff["rule_key"] = [
        _rule_key_for(rule=rule, first_date=first_date)
        for rule, first_date in zip(
            dff["rule"], dff["first_date"], strict=False
        )
    ]
    dff["row_id"] = dff["rule_key"]
    dff["rule_label"] = dff["rule"] + " | " + dff["RuleName"]

    for column in NUMERIC_COLS:
        dff[column] = pd.to_numeric(dff[column], errors="coerce")
    dff[NUMERIC_COLS] = dff[NUMERIC_COLS].fillna(0)

    for perspective_name, config in PERSPECTIVE_CONFIGS.items():
        ci_cols: dict[str, tuple[str, str]] = config["ci_cols"]  # type: ignore[assignment]
        cola_cols: list[str] = config["cola_cols"]  # type: ignore[assignment]
        dominant_labels: dict[str, str] = config["dominant_labels"]  # type: ignore[assignment]
        ae_ratio_col = str(config["ae_ratio_col"])
        scale_col = str(config["scale_col"])

        cola_max = dff[cola_cols].max().max()
        cola_multiplier = 100.0 if float(cola_max) <= 1.5 else 1.0
        display_cola_cols: list[str] = []
        for cola_col in cola_cols:
            display_col = f"{cola_col}_display"
            dff[display_col] = dff[cola_col] * cola_multiplier
            display_cola_cols.append(display_col)

        for level, (lo_col, hi_col) in ci_cols.items():
            dff[f"significance_class_{level}_{perspective_name}"] = np.select(
                [dff[lo_col] > 1.0, dff[hi_col] < 1.0],
                ["Elevated", "Below Expected"],
                default="Uncertain",
            )

        dff[f"ae_gap_{perspective_name}"] = dff[ae_ratio_col] - 1.0
        dff[f"abs_ae_gap_{perspective_name}"] = dff[
            f"ae_gap_{perspective_name}"
        ].abs()
        dff[f"ci_width_{perspective_name}"] = (
            dff[ci_cols["95"][1]] - dff[ci_cols["95"][0]]
        )
        dff[f"impact_score_{perspective_name}"] = (
            np.log1p(dff[scale_col].clip(lower=0))
            * dff[f"abs_ae_gap_{perspective_name}"]
        )

        if dff.empty:
            dff[f"dominant_cola_{perspective_name}"] = ""
            dff[f"dominant_cola_pct_{perspective_name}"] = 0.0
        else:
            dominant_idx = dff[display_cola_cols].values.argmax(axis=1)
            dff[f"dominant_cola_{perspective_name}"] = [
                dominant_labels[cola_cols[idx]] for idx in dominant_idx
            ]
            dff[f"dominant_cola_pct_{perspective_name}"] = dff[
                display_cola_cols
            ].max(axis=1)

        dff[f"confidence_band_{perspective_name}"] = pd.Categorical(
            np.select(
                [
                    dff[ci_cols["95"][0]] > 1,
                    dff[ci_cols["90"][0]] > 1,
                    dff[ci_cols["80"][0]] > 1,
                    dff[ci_cols["95"][1]] < 1,
                    dff[ci_cols["90"][1]] < 1,
                    dff[ci_cols["80"][1]] < 1,
                ],
                [
                    "Elevated 95%",
                    "Elevated 90%",
                    "Elevated 80%",
                    "Below Expected 95%",
                    "Below Expected 90%",
                    "Below Expected 80%",
                ],
                default="Uncertain",
            ),
            categories=CONFIDENCE_BAND_ORDER,
            ordered=True,
        )

    return dff


def apply_filters(
    df: pd.DataFrame,
    *,
    categories: list[str] | None,
    significance_values: list[str] | None,
    search_text: str | None,
    min_hit_count: float | None,
    min_claim_count: float | None,
) -> pd.DataFrame:
    dff = df.copy()

    if categories:
        dff = dff[dff["category"].isin(categories)]

    if significance_values:
        dff = dff[dff["significance_class"].isin(significance_values)]

    if search_text:
        search = str(search_text).strip().lower()
        dff = dff[
            dff["rule"].str.lower().str.contains(search, na=False)
            | dff["RuleName"].str.lower().str.contains(search, na=False)
            | dff["category"].str.lower().str.contains(search, na=False)
        ]

    min_hit = 0.0 if min_hit_count is None else float(min_hit_count)
    min_claim = 0.0 if min_claim_count is None else float(min_claim_count)
    dff = dff[dff["hit_count"] >= min_hit]
    dff = dff[dff["claim_count"] >= min_claim]
    return dff.reset_index(drop=True)


def _load_prepared_df_from_config(
    *, config_id: str
) -> tuple[str, pd.DataFrame]:
    config, file_path = get_dataset_config_with_file(config_id)
    module_config = get_binary_feature_module_config(config)
    mapping = module_config.model_dump()
    source_columns = list(mapping.values())
    if len(set(source_columns)) != len(source_columns):
        raise ValueError(
            "Binary Feature module_config contains duplicate column mappings"
        )

    df = read_dataframe_from_path(file_path=file_path, columns=source_columns)
    renamed = df.rename(
        columns={source: target for target, source in mapping.items()}
    )
    prepared = prepare_rule_df(renamed)
    return config.dataset_name, prepared


def load_prepared_binary_feature_df_from_config(
    *,
    config_id: str,
) -> tuple[str, pd.DataFrame]:
    return _load_prepared_df_from_config(config_id=config_id)


def _build_kpis(df: pd.DataFrame) -> ApiBinaryFeatureKpis:
    if df.empty:
        return ApiBinaryFeatureKpis(
            visible_rule_count=0,
            median_hit_rate=0.0,
            median_claim_count=0.0,
            median_claim_amount=0.0,
            median_ae=0.0,
            elevated_count=0,
            uncertain_count=0,
            below_expected_count=0,
        )

    return ApiBinaryFeatureKpis(
        visible_rule_count=int(len(df)),
        median_hit_rate=float(df["hit_rate"].median()),
        median_claim_count=float(df["claim_count"].median()),
        median_claim_amount=float(df["claim_amount"].median()),
        median_ae=float(df["ae_ratio"].median()),
        elevated_count=int((df["significance_class"] == "Elevated").sum()),
        uncertain_count=int((df["significance_class"] == "Uncertain").sum()),
        below_expected_count=int(
            (df["significance_class"] == "Below Expected").sum()
        ),
    )


def build_binary_feature_kpis(df: pd.DataFrame) -> ApiBinaryFeatureKpis:
    return _build_kpis(df)


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


def _serialize_rows(df: pd.DataFrame) -> list[ApiBinaryFeatureRow]:
    allowed_fields = set(ApiBinaryFeatureRow.model_fields)
    rows: list[ApiBinaryFeatureRow] = []
    for record in df.to_dict(orient="records"):
        clean = {
            key: _serialize_value(value)
            for key, value in record.items()
            if key in allowed_fields
        }
        clean["confidence_band"] = str(clean["confidence_band"])
        rows.append(ApiBinaryFeatureRow.model_validate(clean))
    return rows


def calculate_binary_feature_ae(
    *,
    params: ApiBinaryFeatureCalculateRequest,
) -> ApiBinaryFeatureCalculateResponse:
    from app.modules.binary_feature_ae.service.view_state import (
        build_binary_feature_view_state,
    )

    view_state = build_binary_feature_view_state(params)

    return ApiBinaryFeatureCalculateResponse(
        dataset_name=view_state.dataset_name,
        perspective=params.perspective,
        state_fingerprint=view_state.view_fingerprint,
        available_categories=view_state.available_categories,
        kpis=view_state.kpis,
        rows=_serialize_rows(view_state.filtered_sorted_df),
    )
