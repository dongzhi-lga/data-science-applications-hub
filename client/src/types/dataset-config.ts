export type ModuleId = 'mortality_ae' | 'binary_feature_ae';

export type PerformanceType =
    | 'Mortality A/E Analysis'
    | 'Binary Feature Mortality A/E';

export interface ApiMortalityAeModuleConfig {
    policy_number_column: string | null;
    face_amount_column: string | null;
    mac_column: string;
    mec_column: string;
    man_column: string;
    men_column: string;
    moc_column: string | null;
    cola_m1_column: string | null;
}

export type ApiColumnMapping = ApiMortalityAeModuleConfig;

export interface ApiBinaryFeatureAeModuleConfig {
    rule: string;
    RuleName: string;
    first_date: string;
    category: string;
    hit_count: string;
    hit_rate: string;
    claim_count: string;
    claim_amount: string;
    mec_sum: string;
    ae_ratio_count: string;
    ci_lower_95_count: string;
    ci_upper_95_count: string;
    ci_lower_90_count: string;
    ci_upper_90_count: string;
    ci_lower_80_count: string;
    ci_upper_80_count: string;
    cola_cancer_pct_count: string;
    cola_heart_pct_count: string;
    cola_nervous_system_pct_count: string;
    cola_non_natural_pct_count: string;
    cola_other_medical_pct_count: string;
    cola_respiratory_pct_count: string;
    cola_others_pct_count: string;
    ae_ratio_amount: string;
    ci_lower_95_amount: string;
    ci_upper_95_amount: string;
    ci_lower_90_amount: string;
    ci_upper_90_amount: string;
    ci_lower_80_amount: string;
    ci_upper_80_amount: string;
    cola_cancer_pct_amount: string;
    cola_heart_pct_amount: string;
    cola_nervous_system_pct_amount: string;
    cola_non_natural_pct_amount: string;
    cola_other_medical_pct_amount: string;
    cola_respiratory_pct_amount: string;
    cola_others_pct_amount: string;
}

export type ApiModuleConfig =
    | ApiMortalityAeModuleConfig
    | ApiBinaryFeatureAeModuleConfig;

export interface ApiDatasetConfig {
    id: string;
    dataset_name: string;
    performance_type: PerformanceType;
    file_path: string;
    module_id: ModuleId;
    module_config: ApiModuleConfig;
    created_date: string;
}

export interface ApiCreateDatasetConfigRequest {
    dataset_name: string;
    performance_type: PerformanceType;
    file_path: string;
    module_id: ModuleId;
    module_config: ApiModuleConfig;
}

export interface ApiListDatasetConfigsResults {
    configs: ApiDatasetConfig[];
}

export function isMortalityDatasetConfig(
    config: ApiDatasetConfig,
): config is ApiDatasetConfig & {
    module_id: 'mortality_ae';
    module_config: ApiMortalityAeModuleConfig;
} {
    return config.module_id === 'mortality_ae';
}

export function isBinaryFeatureDatasetConfig(
    config: ApiDatasetConfig,
): config is ApiDatasetConfig & {
    module_id: 'binary_feature_ae';
    module_config: ApiBinaryFeatureAeModuleConfig;
} {
    return config.module_id === 'binary_feature_ae';
}
