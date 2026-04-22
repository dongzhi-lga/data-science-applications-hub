import type {
    ApiBinaryFeatureAeModuleConfig,
    PerformanceType,
} from '@/types/dataset-config';
import type {
    BinaryFeatureCiLevel,
    BinaryFeaturePerspective,
    BinaryFeatureSignificance,
} from '@/types/binary-feature-ae';

export const BINARY_FEATURE_PERFORMANCE_TYPE: PerformanceType =
    'Binary Feature Mortality A/E';

export const SIGNIFICANCE_OPTIONS: BinaryFeatureSignificance[] = [
    'Elevated',
    'Uncertain',
    'Below Expected',
];

export const CI_LEVEL_OPTIONS: BinaryFeatureCiLevel[] = ['95', '90', '80'];

export const PERSPECTIVE_OPTIONS: BinaryFeaturePerspective[] = ['count', 'amount'];

export const PERSPECTIVE_LABELS: Record<BinaryFeaturePerspective, string> = {
    count: 'Count',
    amount: 'Amount',
};

export const CONFIDENCE_BAND_ORDER = [
    'Elevated 95%',
    'Elevated 90%',
    'Elevated 80%',
    'Uncertain',
    'Below Expected 80%',
    'Below Expected 90%',
    'Below Expected 95%',
] as const;

export const CONFIDENCE_BAND_COLORS: Record<string, string> = {
    'Elevated 95%': '#d62728',
    'Elevated 90%': '#ff7f0e',
    'Elevated 80%': '#ffbb78',
    Uncertain: '#aec7e8',
    'Below Expected 80%': '#c5e0b4',
    'Below Expected 90%': '#70ad47',
    'Below Expected 95%': '#375623',
};

export type BinaryFeatureColaKey =
    | 'cola_cancer_pct'
    | 'cola_heart_pct'
    | 'cola_nervous_system_pct'
    | 'cola_non_natural_pct'
    | 'cola_other_medical_pct'
    | 'cola_respiratory_pct'
    | 'cola_others_pct';

export const COLA_DEFINITIONS: Array<{
    key: BinaryFeatureColaKey;
    label: string;
}> = [
    { key: 'cola_cancer_pct', label: 'Cancer' },
    { key: 'cola_heart_pct', label: 'Heart' },
    { key: 'cola_nervous_system_pct', label: 'Nervous System' },
    { key: 'cola_non_natural_pct', label: 'Non-natural' },
    { key: 'cola_other_medical_pct', label: 'Other Medical' },
    { key: 'cola_respiratory_pct', label: 'Respiratory' },
    { key: 'cola_others_pct', label: 'Others' },
];

export type BinaryFeatureFieldDefinition = {
    key: keyof ApiBinaryFeatureAeModuleConfig;
    label: string;
    sourceName: string;
};

export type BinaryFeatureFieldSection = {
    title: string;
    fields: BinaryFeatureFieldDefinition[];
};

export const BINARY_FEATURE_FIELD_SECTIONS: BinaryFeatureFieldSection[] = [
    {
        title: 'Shared Fields',
        fields: [
            { key: 'rule', label: 'Rule', sourceName: 'rule' },
            { key: 'RuleName', label: 'Rule Name', sourceName: 'RuleName' },
            { key: 'first_date', label: 'First Date', sourceName: 'first_date' },
            { key: 'category', label: 'Category', sourceName: 'category' },
            { key: 'hit_count', label: 'Hit Count', sourceName: 'hit_count' },
            { key: 'hit_rate', label: 'Hit Rate', sourceName: 'hit_rate' },
            { key: 'claim_count', label: 'Claim Count', sourceName: 'claim_count' },
            {
                key: 'claim_amount',
                label: 'Claim Amount',
                sourceName: 'claim_amount',
            },
            { key: 'mec_sum', label: 'MEC Sum', sourceName: 'mec_sum' },
            { key: 'men_sum', label: 'MEN Sum', sourceName: 'men_sum' },
        ],
    },
    {
        title: 'Count Perspective',
        fields: [
            {
                key: 'ae_ratio_count',
                label: 'Count A/E Ratio',
                sourceName: 'ae_ratio_count',
            },
            {
                key: 'ci_lower_95_count',
                label: 'Count CI Lower 95',
                sourceName: 'ci_lower_95_count',
            },
            {
                key: 'ci_upper_95_count',
                label: 'Count CI Upper 95',
                sourceName: 'ci_upper_95_count',
            },
            {
                key: 'ci_lower_90_count',
                label: 'Count CI Lower 90',
                sourceName: 'ci_lower_90_count',
            },
            {
                key: 'ci_upper_90_count',
                label: 'Count CI Upper 90',
                sourceName: 'ci_upper_90_count',
            },
            {
                key: 'ci_lower_80_count',
                label: 'Count CI Lower 80',
                sourceName: 'ci_lower_80_count',
            },
            {
                key: 'ci_upper_80_count',
                label: 'Count CI Upper 80',
                sourceName: 'ci_upper_80_count',
            },
            {
                key: 'cola_cancer_pct_count',
                label: 'Count COLA Cancer %',
                sourceName: 'cola_cancer_pct_count',
            },
            {
                key: 'cola_heart_pct_count',
                label: 'Count COLA Heart %',
                sourceName: 'cola_heart_pct_count',
            },
            {
                key: 'cola_nervous_system_pct_count',
                label: 'Count COLA Nervous System %',
                sourceName: 'cola_nervous_system_pct_count',
            },
            {
                key: 'cola_non_natural_pct_count',
                label: 'Count COLA Non-natural %',
                sourceName: 'cola_non-natural_pct_count',
            },
            {
                key: 'cola_other_medical_pct_count',
                label: 'Count COLA Other Medical %',
                sourceName: 'cola_other_medical_pct_count',
            },
            {
                key: 'cola_respiratory_pct_count',
                label: 'Count COLA Respiratory %',
                sourceName: 'cola_respiratory_pct_count',
            },
            {
                key: 'cola_others_pct_count',
                label: 'Count COLA Others %',
                sourceName: 'cola_others_pct_count',
            },
        ],
    },
    {
        title: 'Amount Perspective',
        fields: [
            {
                key: 'ae_ratio_amount',
                label: 'Amount A/E Ratio',
                sourceName: 'ae_ratio_amount',
            },
            {
                key: 'ci_lower_95_amount',
                label: 'Amount CI Lower 95',
                sourceName: 'ci_lower_95_amount',
            },
            {
                key: 'ci_upper_95_amount',
                label: 'Amount CI Upper 95',
                sourceName: 'ci_upper_95_amount',
            },
            {
                key: 'ci_lower_90_amount',
                label: 'Amount CI Lower 90',
                sourceName: 'ci_lower_90_amount',
            },
            {
                key: 'ci_upper_90_amount',
                label: 'Amount CI Upper 90',
                sourceName: 'ci_upper_90_amount',
            },
            {
                key: 'ci_lower_80_amount',
                label: 'Amount CI Lower 80',
                sourceName: 'ci_lower_80_amount',
            },
            {
                key: 'ci_upper_80_amount',
                label: 'Amount CI Upper 80',
                sourceName: 'ci_upper_80_amount',
            },
            {
                key: 'cola_cancer_pct_amount',
                label: 'Amount COLA Cancer %',
                sourceName: 'cola_cancer_pct_amount',
            },
            {
                key: 'cola_heart_pct_amount',
                label: 'Amount COLA Heart %',
                sourceName: 'cola_heart_pct_amount',
            },
            {
                key: 'cola_nervous_system_pct_amount',
                label: 'Amount COLA Nervous System %',
                sourceName: 'cola_nervous_system_pct_amount',
            },
            {
                key: 'cola_non_natural_pct_amount',
                label: 'Amount COLA Non-natural %',
                sourceName: 'cola_non-natural_pct_amount',
            },
            {
                key: 'cola_other_medical_pct_amount',
                label: 'Amount COLA Other Medical %',
                sourceName: 'cola_other_medical_pct_amount',
            },
            {
                key: 'cola_respiratory_pct_amount',
                label: 'Amount COLA Respiratory %',
                sourceName: 'cola_respiratory_pct_amount',
            },
            {
                key: 'cola_others_pct_amount',
                label: 'Amount COLA Others %',
                sourceName: 'cola_others_pct_amount',
            },
        ],
    },
];

export const BINARY_FEATURE_FIELD_DEFINITIONS = BINARY_FEATURE_FIELD_SECTIONS.flatMap(
    (section) => section.fields,
);
