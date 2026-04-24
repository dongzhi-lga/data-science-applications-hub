from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ApiBinaryFeatureAiAction(StrEnum):
    SUMMARIZE_VIEW = "summarize_view"
    EXPLAIN_FOCUSED_RULE = "explain_focused_rule"
    EXPLAIN_RULE = "explain_rule"
    COMPARE_RULES = "compare_rules"
    ANALYZE_DIVERGENCE = "analyze_divergence"


class ApiBinaryFeatureAiSourceMode(StrEnum):
    LLM = "llm"
    FALLBACK = "fallback"


class ApiBinaryFeatureAiSeverity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEUTRAL = "neutral"


class ApiBinaryFeatureAiReasonType(StrEnum):
    FOCUSED_RULE = "focused_rule"
    VISIBLE_PATTERN = "visible_pattern"
    SELECTED_FOR_COMPARISON = "selected_for_comparison"
    COUNT_AMOUNT_DIVERGENCE = "count_amount_divergence"
    ELEVATED_RELATIVE_TO_EXPECTED = "elevated_relative_to_expected"
    BELOW_EXPECTED = "below_expected"
    UNCERTAIN_INTERVAL = "uncertain_interval"
    HIGH_MATERIALITY = "high_materiality"
    WIDE_UNCERTAINTY = "wide_uncertainty"
    REFERENCE_CONTEXT_USED = "reference_context_used"


class ApiBinaryFeatureAiBaseFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config_id: str
    perspective: Literal["count", "amount"] = "count"
    ci_level: Literal["95", "90", "80"] = "95"
    categories: list[str] = Field(default_factory=list)
    significance_values: list[
        Literal["Elevated", "Uncertain", "Below Expected"]
    ] = Field(
        default_factory=lambda: ["Elevated", "Uncertain", "Below Expected"]
    )
    search_text: str | None = None
    min_hit_count: float | None = 0
    min_claim_count: float | None = 0


class ApiBinaryFeatureAiSummarizeViewRequest(ApiBinaryFeatureAiBaseFilters):
    model_config = ConfigDict(extra="forbid")


class ApiBinaryFeatureAiExplainRuleRequest(ApiBinaryFeatureAiBaseFilters):
    model_config = ConfigDict(extra="forbid")

    row_id: str


class ApiBinaryFeatureAiCompareRulesRequest(ApiBinaryFeatureAiBaseFilters):
    model_config = ConfigDict(extra="forbid")

    row_ids: list[str] = Field(min_length=2, max_length=5)


class ApiBinaryFeatureAiAnalyzeDivergenceRequest(ApiBinaryFeatureAiBaseFilters):
    model_config = ConfigDict(extra="forbid")

    row_id: str


class ApiBinaryFeatureAiEvidenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_id: str
    rule_label: str
    reason_type: ApiBinaryFeatureAiReasonType
    reason_label: str
    severity: ApiBinaryFeatureAiSeverity


class ApiBinaryFeatureAiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_type: ApiBinaryFeatureAiAction
    state_fingerprint: str
    source_mode: ApiBinaryFeatureAiSourceMode
    summary_text: str
    key_findings: list[str] = Field(default_factory=list)
    caution_flags: list[str] = Field(default_factory=list)
    next_review_steps: list[str] = Field(default_factory=list)
    evidence_refs: list[ApiBinaryFeatureAiEvidenceRef] = Field(
        default_factory=list
    )
    used_reference_context: bool = False
    reference_sources: list[str] = Field(default_factory=list)
    validation_notes: list[str] = Field(default_factory=list)


class BinaryFeatureAiReferenceSnippet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str
    source_type: str
    matched_on: str
    text: str


class BinaryFeatureAiRuleBaselines(BaseModel):
    model_config = ConfigDict(extra="forbid")

    impact_score_percentile: float
    hit_count_percentile: float
    claim_count_percentile: float
    claim_amount_percentile: float
    ci_width_percentile: float
    low_volume_flag: bool
    high_uncertainty_flag: bool
    concentrated_cola_flag: bool


class BinaryFeatureAiSkillDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    action_type: ApiBinaryFeatureAiAction
    version: str
    model_profile: str
    temperature: float
    response_schema: str
    body: str


class BinaryFeatureAiPacketBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_type: ApiBinaryFeatureAiAction
    state_fingerprint: str
    dataset_name: str
    perspective: Literal["count", "amount"]
    ci_level: Literal["95", "90", "80"]
    active_filters: dict[str, object]
    kpis: dict[str, object]
    used_reference_context: bool = False
    reference_snippets: list[BinaryFeatureAiReferenceSnippet] = Field(
        default_factory=list
    )
    reference_sources: list[str] = Field(default_factory=list)


class BinaryFeatureAiSummarizeViewPacket(BinaryFeatureAiPacketBase):
    model_config = ConfigDict(extra="forbid")

    visible_rule_count: int
    significance_counts: dict[str, int]
    top_rows: list[dict[str, object]]


class BinaryFeatureAiExplainFocusedRulePacket(BinaryFeatureAiPacketBase):
    model_config = ConfigDict(extra="forbid")

    focused_row: dict[str, object]
    baselines: BinaryFeatureAiRuleBaselines
    visible_rule_count: int


class BinaryFeatureAiCompareRulesPacket(BinaryFeatureAiPacketBase):
    model_config = ConfigDict(extra="forbid")

    rule_rows: list[dict[str, object]]


class BinaryFeatureAiAnalyzeDivergencePacket(BinaryFeatureAiPacketBase):
    model_config = ConfigDict(extra="forbid")

    count_row: dict[str, object]
    amount_row: dict[str, object]
    divergence_metrics: dict[str, object]


BinaryFeatureAiExplainRulePacket = BinaryFeatureAiExplainFocusedRulePacket
