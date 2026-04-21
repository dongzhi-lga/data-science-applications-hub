from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest

from app.core.models.dataset_config import (
    ApiBinaryFeatureAeModuleConfig,
    ApiCreateDatasetConfigRequest,
    ModuleId,
    PerformanceType,
)
from app.core.service.dataset_config import create_dataset_config, save_uploaded_file
from app.modules.binary_feature_ae.models.triage import (
    ApiBinaryFeatureCalculateRequest,
    ApiBinaryFeaturePerspective,
    ApiBinaryFeatureSignificance,
)
from app.modules.binary_feature_ae.service.binary_calc import (
    apply_filters,
    calculate_binary_feature_ae,
    prepare_rule_df,
)


def _sample_binary_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "rule": "R1",
                "RuleName": "Rule One",
                "first_date": "2024-01-01",
                "category": "Cancer",
                "hit_count": 100,
                "hit_rate": 0.12,
                "claim_count": 20,
                "claim_amount": 500000,
                "mec_sum": 18,
                "ae_ratio_count": 1.4,
                "ci_lower_95_count": 1.2,
                "ci_upper_95_count": 1.6,
                "ci_lower_90_count": 1.22,
                "ci_upper_90_count": 1.58,
                "ci_lower_80_count": 1.25,
                "ci_upper_80_count": 1.55,
                "ae_ratio_amount": 0.78,
                "ci_lower_95_amount": 0.6,
                "ci_upper_95_amount": 0.95,
                "ci_lower_90_amount": 0.62,
                "ci_upper_90_amount": 0.93,
                "ci_lower_80_amount": 0.65,
                "ci_upper_80_amount": 0.9,
                "cola_cancer_pct_count": 0.60,
                "cola_heart_pct_count": 0.20,
                "cola_nervous_system_pct_count": 0.05,
                "cola_non_natural_pct_count": 0.03,
                "cola_other_medical_pct_count": 0.04,
                "cola_respiratory_pct_count": 0.05,
                "cola_others_pct_count": 0.03,
                "cola_cancer_pct_amount": 0.20,
                "cola_heart_pct_amount": 0.45,
                "cola_nervous_system_pct_amount": 0.05,
                "cola_non_natural_pct_amount": 0.05,
                "cola_other_medical_pct_amount": 0.10,
                "cola_respiratory_pct_amount": 0.10,
                "cola_others_pct_amount": 0.05,
            },
            {
                "rule": "R2",
                "RuleName": "Rule Two",
                "first_date": "2024-02-01",
                "category": "Cardio",
                "hit_count": 10,
                "hit_rate": 0.02,
                "claim_count": 6,
                "claim_amount": 200000,
                "mec_sum": 8,
                "ae_ratio_count": 0.7,
                "ci_lower_95_count": 0.5,
                "ci_upper_95_count": 0.8,
                "ci_lower_90_count": 0.52,
                "ci_upper_90_count": 0.82,
                "ci_lower_80_count": 0.56,
                "ci_upper_80_count": 0.88,
                "ae_ratio_amount": 1.35,
                "ci_lower_95_amount": 1.1,
                "ci_upper_95_amount": 1.55,
                "ci_lower_90_amount": 1.12,
                "ci_upper_90_amount": 1.52,
                "ci_lower_80_amount": 1.15,
                "ci_upper_80_amount": 1.48,
                "cola_cancer_pct_count": 0.10,
                "cola_heart_pct_count": 0.55,
                "cola_nervous_system_pct_count": 0.05,
                "cola_non_natural_pct_count": 0.05,
                "cola_other_medical_pct_count": 0.10,
                "cola_respiratory_pct_count": 0.10,
                "cola_others_pct_count": 0.05,
                "cola_cancer_pct_amount": 0.50,
                "cola_heart_pct_amount": 0.20,
                "cola_nervous_system_pct_amount": 0.05,
                "cola_non_natural_pct_amount": 0.05,
                "cola_other_medical_pct_amount": 0.05,
                "cola_respiratory_pct_amount": 0.10,
                "cola_others_pct_amount": 0.05,
            },
            {
                "rule": "R3",
                "RuleName": "Rule Three",
                "first_date": "2024-03-01",
                "category": "Cancer",
                "hit_count": 5,
                "hit_rate": 0.01,
                "claim_count": 3,
                "claim_amount": 25000,
                "mec_sum": 4,
                "ae_ratio_count": 1.05,
                "ci_lower_95_count": 0.8,
                "ci_upper_95_count": 1.3,
                "ci_lower_90_count": 0.9,
                "ci_upper_90_count": 1.2,
                "ci_lower_80_count": 1.01,
                "ci_upper_80_count": 1.1,
                "ae_ratio_amount": 1.02,
                "ci_lower_95_amount": 0.9,
                "ci_upper_95_amount": 1.15,
                "ci_lower_90_amount": 0.94,
                "ci_upper_90_amount": 1.12,
                "ci_lower_80_amount": 0.97,
                "ci_upper_80_amount": 1.09,
                "cola_cancer_pct_count": 0.15,
                "cola_heart_pct_count": 0.15,
                "cola_nervous_system_pct_count": 0.20,
                "cola_non_natural_pct_count": 0.20,
                "cola_other_medical_pct_count": 0.10,
                "cola_respiratory_pct_count": 0.10,
                "cola_others_pct_count": 0.10,
                "cola_cancer_pct_amount": 0.15,
                "cola_heart_pct_amount": 0.15,
                "cola_nervous_system_pct_amount": 0.20,
                "cola_non_natural_pct_amount": 0.20,
                "cola_other_medical_pct_amount": 0.10,
                "cola_respiratory_pct_amount": 0.10,
                "cola_others_pct_amount": 0.10,
            },
        ]
    )


def _module_config() -> ApiBinaryFeatureAeModuleConfig:
    return ApiBinaryFeatureAeModuleConfig(
        rule="rule",
        RuleName="RuleName",
        first_date="first_date",
        category="category",
        hit_count="hit_count",
        hit_rate="hit_rate",
        claim_count="claim_count",
        claim_amount="claim_amount",
        mec_sum="mec_sum",
        ae_ratio_count="ae_ratio_count",
        ci_lower_95_count="ci_lower_95_count",
        ci_upper_95_count="ci_upper_95_count",
        ci_lower_90_count="ci_lower_90_count",
        ci_upper_90_count="ci_upper_90_count",
        ci_lower_80_count="ci_lower_80_count",
        ci_upper_80_count="ci_upper_80_count",
        cola_cancer_pct_count="cola_cancer_pct_count",
        cola_heart_pct_count="cola_heart_pct_count",
        cola_nervous_system_pct_count="cola_nervous_system_pct_count",
        cola_non_natural_pct_count="cola_non-natural_pct_count",
        cola_other_medical_pct_count="cola_other_medical_pct_count",
        cola_respiratory_pct_count="cola_respiratory_pct_count",
        cola_others_pct_count="cola_others_pct_count",
        ae_ratio_amount="ae_ratio_amount",
        ci_lower_95_amount="ci_lower_95_amount",
        ci_upper_95_amount="ci_upper_95_amount",
        ci_lower_90_amount="ci_lower_90_amount",
        ci_upper_90_amount="ci_upper_90_amount",
        ci_lower_80_amount="ci_lower_80_amount",
        ci_upper_80_amount="ci_upper_80_amount",
        cola_cancer_pct_amount="cola_cancer_pct_amount",
        cola_heart_pct_amount="cola_heart_pct_amount",
        cola_nervous_system_pct_amount="cola_nervous_system_pct_amount",
        cola_non_natural_pct_amount="cola_non-natural_pct_amount",
        cola_other_medical_pct_amount="cola_other_medical_pct_amount",
        cola_respiratory_pct_amount="cola_respiratory_pct_amount",
        cola_others_pct_amount="cola_others_pct_amount",
    )


def test_prepare_rule_df_requires_all_columns() -> None:
    with pytest.raises(ValueError, match="Missing required columns"):
        prepare_rule_df(pd.DataFrame({"rule": ["R1"]}))


def test_prepare_rule_df_normalizes_and_derives_metrics() -> None:
    prepared = prepare_rule_df(_sample_binary_df())

    top = prepared.loc[prepared["rule"] == "R1"].iloc[0]
    assert top["rule_key"] == top["row_id"]
    assert top["significance_class_95_count"] == "Elevated"
    assert top["significance_class_95_amount"] == "Below Expected"
    assert top["confidence_band_count"] == "Elevated 95%"
    assert top["confidence_band_amount"] == "Below Expected 95%"
    assert top["dominant_cola_count"] == "Cancer"
    assert top["dominant_cola_amount"] == "Heart"
    assert top["dominant_cola_pct_count"] == pytest.approx(60.0)
    assert top["dominant_cola_pct_amount"] == pytest.approx(45.0)
    assert top["cola_cancer_pct_count_display"] == pytest.approx(60.0)
    assert top["cola_heart_pct_amount_display"] == pytest.approx(45.0)

    mid = prepared.loc[prepared["rule"] == "R3"].iloc[0]
    assert mid["significance_class_95_count"] == "Uncertain"
    assert mid["significance_class_80_count"] == "Elevated"
    assert mid["confidence_band_count"] == "Elevated 80%"

    low = prepared.loc[prepared["rule"] == "R2"].iloc[0]
    assert low["significance_class_95_count"] == "Below Expected"
    assert low["significance_class_95_amount"] == "Elevated"
    assert low["impact_score_amount"] > top["impact_score_amount"]


def test_prepare_rule_df_generates_deterministic_rule_keys() -> None:
    prepared = prepare_rule_df(_sample_binary_df())
    shuffled = prepare_rule_df(_sample_binary_df().sample(frac=1, random_state=7))

    prepared_keys = (
        prepared[["rule", "first_date", "rule_key", "row_id"]]
        .sort_values(["rule", "first_date"])
        .reset_index(drop=True)
    )
    shuffled_keys = (
        shuffled[["rule", "first_date", "rule_key", "row_id"]]
        .sort_values(["rule", "first_date"])
        .reset_index(drop=True)
    )

    assert prepared_keys.equals(shuffled_keys)
    assert (prepared_keys["rule_key"] == prepared_keys["row_id"]).all()


def test_apply_filters_matches_shared_filter_behavior() -> None:
    prepared = prepare_rule_df(_sample_binary_df())
    working = prepared.copy()
    working["significance_class"] = working["significance_class_95_count"]

    filtered = apply_filters(
        working,
        categories=["Cancer"],
        significance_values=["Elevated"],
        search_text="rule one",
        min_hit_count=50,
        min_claim_count=10,
    )

    assert filtered["rule"].tolist() == ["R1"]


def test_calculate_binary_feature_ae_switches_perspective_aliases_and_sorting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))

    source_df = _sample_binary_df().rename(
        columns={
            "cola_non_natural_pct_count": "cola_non-natural_pct_count",
            "cola_non_natural_pct_amount": "cola_non-natural_pct_amount",
        }
    )
    csv_bytes = source_df.to_csv(index=False).encode("utf-8")

    request = ApiCreateDatasetConfigRequest(
        dataset_name="binary-demo",
        performance_type=PerformanceType.BINARY_FEATURE_AE,
        file_path="binary.csv",
        module_id=ModuleId.BINARY_FEATURE_AE,
        module_config=_module_config(),
    )
    config = create_dataset_config(request)
    save_uploaded_file(config.id, BytesIO(csv_bytes), "binary.csv")

    count_response = calculate_binary_feature_ae(
        params=ApiBinaryFeatureCalculateRequest(
            config_id=config.id,
            perspective=ApiBinaryFeaturePerspective.COUNT,
            categories=[],
            significance_values=[
                ApiBinaryFeatureSignificance.ELEVATED,
                ApiBinaryFeatureSignificance.UNCERTAIN,
                ApiBinaryFeatureSignificance.BELOW_EXPECTED,
            ],
            min_hit_count=0,
            min_claim_count=0,
        )
    )
    amount_response = calculate_binary_feature_ae(
        params=ApiBinaryFeatureCalculateRequest(
            config_id=config.id,
            perspective=ApiBinaryFeaturePerspective.AMOUNT,
            categories=[],
            significance_values=[
                ApiBinaryFeatureSignificance.ELEVATED,
                ApiBinaryFeatureSignificance.UNCERTAIN,
                ApiBinaryFeatureSignificance.BELOW_EXPECTED,
            ],
            min_hit_count=0,
            min_claim_count=0,
        )
    )

    assert count_response.perspective == ApiBinaryFeaturePerspective.COUNT
    assert amount_response.perspective == ApiBinaryFeaturePerspective.AMOUNT

    assert count_response.rows[0].rule == "R1"
    assert amount_response.rows[0].rule == "R2"

    count_r1 = next(row for row in count_response.rows if row.rule == "R1")
    amount_r1 = next(row for row in amount_response.rows if row.rule == "R1")
    amount_r2 = next(row for row in amount_response.rows if row.rule == "R2")

    assert count_r1.ae_ratio == pytest.approx(1.4)
    assert count_r1.significance_class == ApiBinaryFeatureSignificance.ELEVATED
    assert count_r1.dominant_cola == "Cancer"
    assert count_r1.dominant_cola_pct == pytest.approx(60.0)
    assert count_r1.ci_lower == pytest.approx(count_r1.ci_lower_95)

    assert amount_r1.ae_ratio == pytest.approx(0.78)
    assert amount_r1.significance_class == ApiBinaryFeatureSignificance.BELOW_EXPECTED
    assert amount_r1.dominant_cola == "Heart"
    assert amount_r1.dominant_cola_pct == pytest.approx(45.0)
    assert amount_r1.ci_lower == pytest.approx(amount_r1.ci_lower_95)

    assert amount_r2.significance_class == ApiBinaryFeatureSignificance.ELEVATED
    assert count_response.kpis.median_claim_amount == pytest.approx(200000.0)
    assert amount_response.kpis.median_claim_amount == pytest.approx(200000.0)
    assert count_response.kpis.median_ae == pytest.approx(1.05)
    assert amount_response.kpis.median_ae == pytest.approx(1.02)


def test_calculate_binary_feature_ae_from_saved_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))

    source_df = _sample_binary_df().rename(
        columns={
            "cola_non_natural_pct_count": "cola_non-natural_pct_count",
            "cola_non_natural_pct_amount": "cola_non-natural_pct_amount",
        }
    )
    csv_bytes = source_df.to_csv(index=False).encode("utf-8")

    request = ApiCreateDatasetConfigRequest(
        dataset_name="binary-demo",
        performance_type=PerformanceType.BINARY_FEATURE_AE,
        file_path="binary.csv",
        module_id=ModuleId.BINARY_FEATURE_AE,
        module_config=_module_config(),
    )
    config = create_dataset_config(request)
    save_uploaded_file(config.id, BytesIO(csv_bytes), "binary.csv")

    response = calculate_binary_feature_ae(
        params=ApiBinaryFeatureCalculateRequest(
            config_id=config.id,
            perspective=ApiBinaryFeaturePerspective.COUNT,
            categories=["Cancer"],
            significance_values=[
                ApiBinaryFeatureSignificance.ELEVATED,
                ApiBinaryFeatureSignificance.UNCERTAIN,
            ],
            min_hit_count=0,
            min_claim_count=0,
        )
    )

    assert response.dataset_name == "binary-demo"
    assert response.available_categories == ["Cancer", "Cardio"]
    assert response.perspective == ApiBinaryFeaturePerspective.COUNT
    assert response.kpis.visible_rule_count == 2
    assert response.kpis.median_claim_amount == pytest.approx(262500.0)
    assert {row.rule for row in response.rows} == {"R1", "R3"}
    assert response.rows[0].ci_lower == response.rows[0].ci_lower_95
