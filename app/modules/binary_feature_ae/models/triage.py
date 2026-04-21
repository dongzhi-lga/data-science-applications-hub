from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ApiBinaryFeatureCiLevel(StrEnum):
    CI_95 = "95"
    CI_90 = "90"
    CI_80 = "80"


class ApiBinaryFeaturePerspective(StrEnum):
    COUNT = "count"
    AMOUNT = "amount"


class ApiBinaryFeatureSignificance(StrEnum):
    ELEVATED = "Elevated"
    UNCERTAIN = "Uncertain"
    BELOW_EXPECTED = "Below Expected"


class ApiBinaryFeatureKpis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    visible_rule_count: int
    median_hit_rate: float
    median_claim_count: float
    median_claim_amount: float
    median_ae: float
    elevated_count: int
    uncertain_count: int
    below_expected_count: int


class ApiBinaryFeatureCalculateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config_id: str
    perspective: ApiBinaryFeaturePerspective = ApiBinaryFeaturePerspective.COUNT
    ci_level: ApiBinaryFeatureCiLevel = ApiBinaryFeatureCiLevel.CI_95
    categories: list[str] = Field(default_factory=list)
    significance_values: list[ApiBinaryFeatureSignificance] = Field(
        default_factory=lambda: [
            ApiBinaryFeatureSignificance.ELEVATED,
            ApiBinaryFeatureSignificance.UNCERTAIN,
            ApiBinaryFeatureSignificance.BELOW_EXPECTED,
        ]
    )
    search_text: str | None = None
    min_hit_count: float | None = 0
    min_claim_count: float | None = 0


class ApiBinaryFeatureRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_id: str
    rule_key: str
    rule: str
    RuleName: str
    rule_label: str
    first_date: str
    category: str
    hit_count: float
    hit_rate: float
    claim_count: float
    claim_amount: float
    mec_sum: float
    ae_ratio: float
    ci_lower_95: float
    ci_upper_95: float
    ci_lower_90: float
    ci_upper_90: float
    ci_lower_80: float
    ci_upper_80: float
    cola_cancer_pct: float
    cola_heart_pct: float
    cola_nervous_system_pct: float
    cola_non_natural_pct: float
    cola_other_medical_pct: float
    cola_respiratory_pct: float
    cola_others_pct: float
    cola_cancer_pct_display: float
    cola_heart_pct_display: float
    cola_nervous_system_pct_display: float
    cola_non_natural_pct_display: float
    cola_other_medical_pct_display: float
    cola_respiratory_pct_display: float
    cola_others_pct_display: float
    significance_class_95: ApiBinaryFeatureSignificance
    significance_class_90: ApiBinaryFeatureSignificance
    significance_class_80: ApiBinaryFeatureSignificance
    significance_class: ApiBinaryFeatureSignificance
    ae_gap: float
    abs_ae_gap: float
    ci_width: float
    impact_score: float
    dominant_cola: str
    dominant_cola_pct: float
    confidence_band: str
    ci_lower: float
    ci_upper: float


class ApiBinaryFeatureCalculateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    perspective: ApiBinaryFeaturePerspective
    available_categories: list[str]
    kpis: ApiBinaryFeatureKpis
    rows: list[ApiBinaryFeatureRow]
