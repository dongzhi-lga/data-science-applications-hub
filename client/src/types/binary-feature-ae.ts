export type BinaryFeatureCiLevel = '95' | '90' | '80';
export type BinaryFeaturePerspective = 'count' | 'amount';
export type BinaryFeatureSignificance =
    | 'Elevated'
    | 'Uncertain'
    | 'Below Expected';
export type BinaryFeatureAiAction =
    | 'summarize_view'
    | 'explain_rule'
    | 'compare_rules'
    | 'analyze_divergence';
export type BinaryFeatureAiSourceMode = 'llm' | 'fallback';
export type BinaryFeatureAiSeverity = 'high' | 'medium' | 'low' | 'neutral';
export type BinaryFeatureAiReasonType =
    | 'top_impact'
    | 'elevated_95'
    | 'elevated_90'
    | 'elevated_80'
    | 'below_expected'
    | 'wide_uncertainty'
    | 'dominant_cola_concentration'
    | 'count_amount_divergence'
    | 'selected_for_comparison';

export interface ApiBinaryFeatureKpis {
    visible_rule_count: number;
    median_hit_rate: number;
    median_claim_count: number;
    median_claim_amount: number;
    median_ae: number;
    elevated_count: number;
    uncertain_count: number;
    below_expected_count: number;
}

export interface ApiBinaryFeatureCalculateRequest {
    config_id: string;
    perspective: BinaryFeaturePerspective;
    ci_level: BinaryFeatureCiLevel;
    categories: string[];
    significance_values: BinaryFeatureSignificance[];
    search_text: string | null;
    min_hit_count: number | null;
    min_claim_count: number | null;
}

export interface ApiBinaryFeatureRow {
    row_id: string;
    rule_key: string;
    rule: string;
    RuleName: string;
    rule_label: string;
    first_date: string;
    category: string;
    hit_count: number;
    hit_rate: number;
    claim_count: number;
    claim_amount: number;
    men_sum: number;
    mec_sum: number;
    ae_ratio: number;
    ci_lower_95: number;
    ci_upper_95: number;
    ci_lower_90: number;
    ci_upper_90: number;
    ci_lower_80: number;
    ci_upper_80: number;
    cola_cancer_pct: number;
    cola_heart_pct: number;
    cola_nervous_system_pct: number;
    cola_non_natural_pct: number;
    cola_other_medical_pct: number;
    cola_respiratory_pct: number;
    cola_others_pct: number;
    cola_cancer_pct_display: number;
    cola_heart_pct_display: number;
    cola_nervous_system_pct_display: number;
    cola_non_natural_pct_display: number;
    cola_other_medical_pct_display: number;
    cola_respiratory_pct_display: number;
    cola_others_pct_display: number;
    significance_class_95: BinaryFeatureSignificance;
    significance_class_90: BinaryFeatureSignificance;
    significance_class_80: BinaryFeatureSignificance;
    significance_class: BinaryFeatureSignificance;
    ae_gap: number;
    abs_ae_gap: number;
    ci_width: number;
    impact_score: number;
    dominant_cola: string;
    dominant_cola_pct: number;
    confidence_band: string;
    ci_lower: number;
    ci_upper: number;
}

export interface ApiBinaryFeatureCalculateResponse {
    dataset_name: string;
    perspective: BinaryFeaturePerspective;
    state_fingerprint: string;
    available_categories: string[];
    kpis: ApiBinaryFeatureKpis;
    rows: ApiBinaryFeatureRow[];
}

export interface ApiBinaryFeatureAiEvidenceRef {
    row_id: string;
    rule_label: string;
    reason_type: BinaryFeatureAiReasonType;
    reason_label: string;
    severity: BinaryFeatureAiSeverity;
}

export interface ApiBinaryFeatureAiExplainRuleRequest {
    config_id: string;
    perspective: BinaryFeaturePerspective;
    ci_level: BinaryFeatureCiLevel;
    categories: string[];
    significance_values: BinaryFeatureSignificance[];
    search_text: string | null;
    min_hit_count: number | null;
    min_claim_count: number | null;
    row_id: string;
}

export interface ApiBinaryFeatureAiResponse {
    action_type: BinaryFeatureAiAction;
    state_fingerprint: string;
    source_mode: BinaryFeatureAiSourceMode;
    summary_text: string;
    key_findings: string[];
    caution_flags: string[];
    next_review_steps: string[];
    evidence_refs: ApiBinaryFeatureAiEvidenceRef[];
    used_reference_context: boolean;
    reference_sources: string[];
}
