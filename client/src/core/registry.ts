import type { Component } from 'vue';

import type {
    ApiBinaryFeatureAeModuleConfig,
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
    ApiMortalityAeModuleConfig,
    ModuleId,
    PerformanceType,
} from '@/types/dataset-config';
import {
    isBinaryFeatureDatasetConfig,
    isMortalityDatasetConfig,
} from '@/types/dataset-config';
import type { ApiDatasetSchemaResults } from '@/types/datasets';
import { postAeUploadSchema } from '@/modules/mortality-ae/api';

import type { ApiCoreDatasetSchemaResults } from './types/schema';

export type ModuleFieldError = {
    field: string;
    message: string;
};

export type ModuleValidationResult = {
    summary: string[];
    fieldErrors: ModuleFieldError[];
} | null;

export type MortalityAeSetupState = {
    policy_number_column: string | null;
    face_amount_column: string | null;
    mac_column: string | null;
    mec_column: string | null;
    man_column: string | null;
    men_column: string | null;
    moc_column: string | null;
    cola_m1_column: string | null;
};

export type BinaryFeatureAeSetupState = {
    rule: string | null;
    RuleName: string | null;
    first_date: string | null;
    category: string | null;
    hit_count: string | null;
    hit_rate: string | null;
    claim_count: string | null;
    mec_sum: string | null;
    ae_ratio: string | null;
    ci_lower_95: string | null;
    ci_upper_95: string | null;
    ci_lower_90: string | null;
    ci_upper_90: string | null;
    ci_lower_80: string | null;
    ci_upper_80: string | null;
    cola_cancer_pct: string | null;
    cola_heart_pct: string | null;
    cola_nervous_system_pct: string | null;
    cola_non_natural_pct: string | null;
    cola_other_medical_pct: string | null;
    cola_respiratory_pct: string | null;
    cola_others_pct: string | null;
};

export type AsyncSetupComponent = () => Promise<{ default: Component }>;

export type AnalysisModuleDefinition<TSetupState = unknown, TSetupContext = unknown> = {
    id: ModuleId;
    label: string;
    status: 'active' | 'planned' | 'hidden';
    analysisRoute: string;
    performanceType: PerformanceType;
    setupComponent: AsyncSetupComponent;
    createInitialSetupState: () => TSetupState;
    validateSetupState: (state: TSetupState) => ModuleValidationResult;
    buildCreateRequest: (args: {
        datasetName: string;
        uploadedFileName: string;
        setupState: TSetupState;
    }) => ApiCreateDatasetConfigRequest;
    loadSetupStateFromExistingConfig?: (config: ApiDatasetConfig) => TSetupState;
    loadSetupContext?: (
        file: File,
        schema: ApiCoreDatasetSchemaResults,
    ) => Promise<TSetupContext>;
};

export type AnyAnalysisModuleDefinition = AnalysisModuleDefinition<any, any>;

function createInitialMortalitySetupState(): MortalityAeSetupState {
    return {
        policy_number_column: null,
        face_amount_column: null,
        mac_column: null,
        mec_column: null,
        man_column: null,
        men_column: null,
        moc_column: null,
        cola_m1_column: null,
    };
}

function validateMortalitySetupState(
    state: MortalityAeSetupState,
): ModuleValidationResult {
    const fieldErrors: ModuleFieldError[] = [];
    const requiredFields: Array<keyof MortalityAeSetupState> = [
        'mac_column',
        'mec_column',
        'man_column',
        'men_column',
    ];

    for (const field of requiredFields) {
        if (!state[field]) {
            fieldErrors.push({ field, message: 'Required' });
        }
    }

    if (fieldErrors.length === 0) {
        return null;
    }

    return {
        summary: ['Complete the required mortality column mappings.'],
        fieldErrors,
    };
}

function buildMortalityCreateRequest(args: {
    datasetName: string;
    uploadedFileName: string;
    setupState: MortalityAeSetupState;
}): ApiCreateDatasetConfigRequest {
    return {
        dataset_name: args.datasetName,
        performance_type: 'Mortality A/E Analysis',
        file_path: args.uploadedFileName,
        module_id: 'mortality_ae',
        module_config: {
            policy_number_column: args.setupState.policy_number_column,
            face_amount_column: args.setupState.face_amount_column,
            mac_column: args.setupState.mac_column ?? '',
            mec_column: args.setupState.mec_column ?? '',
            man_column: args.setupState.man_column ?? '',
            men_column: args.setupState.men_column ?? '',
            moc_column: args.setupState.moc_column,
            cola_m1_column: args.setupState.cola_m1_column,
        },
    };
}

function loadMortalitySetupStateFromConfig(
    config: ApiDatasetConfig,
): MortalityAeSetupState {
    if (!isMortalityDatasetConfig(config)) {
        return createInitialMortalitySetupState();
    }

    return {
        policy_number_column: config.module_config.policy_number_column,
        face_amount_column: config.module_config.face_amount_column,
        mac_column: config.module_config.mac_column,
        mec_column: config.module_config.mec_column,
        man_column: config.module_config.man_column,
        men_column: config.module_config.men_column,
        moc_column: config.module_config.moc_column,
        cola_m1_column: config.module_config.cola_m1_column,
    };
}

function createInitialBinaryFeatureSetupState(): BinaryFeatureAeSetupState {
    return {
        rule: null,
        RuleName: null,
        first_date: null,
        category: null,
        hit_count: null,
        hit_rate: null,
        claim_count: null,
        mec_sum: null,
        ae_ratio: null,
        ci_lower_95: null,
        ci_upper_95: null,
        ci_lower_90: null,
        ci_upper_90: null,
        ci_lower_80: null,
        ci_upper_80: null,
        cola_cancer_pct: null,
        cola_heart_pct: null,
        cola_nervous_system_pct: null,
        cola_non_natural_pct: null,
        cola_other_medical_pct: null,
        cola_respiratory_pct: null,
        cola_others_pct: null,
    };
}

const binaryFeatureRequiredFields: Array<keyof BinaryFeatureAeSetupState> = [
    'rule',
    'RuleName',
    'first_date',
    'category',
    'hit_count',
    'hit_rate',
    'claim_count',
    'mec_sum',
    'ae_ratio',
    'ci_lower_95',
    'ci_upper_95',
    'ci_lower_90',
    'ci_upper_90',
    'ci_lower_80',
    'ci_upper_80',
    'cola_cancer_pct',
    'cola_heart_pct',
    'cola_nervous_system_pct',
    'cola_non_natural_pct',
    'cola_other_medical_pct',
    'cola_respiratory_pct',
    'cola_others_pct',
];

function validateBinaryFeatureSetupState(
    state: BinaryFeatureAeSetupState,
): ModuleValidationResult {
    const fieldErrors: ModuleFieldError[] = [];

    for (const field of binaryFeatureRequiredFields) {
        if (!state[field]) {
            fieldErrors.push({ field, message: 'Required' });
        }
    }

    const selectedColumns = Object.entries(state)
        .filter(([, value]) => Boolean(value))
        .map(([field, value]) => ({
            field,
            value: value as string,
        }));
    const seenColumns = new Map<string, string>();
    for (const entry of selectedColumns) {
        const existing = seenColumns.get(entry.value);
        if (existing) {
            fieldErrors.push({
                field: entry.field,
                message: `Already assigned to ${existing}`,
            });
        } else {
            seenColumns.set(entry.value, entry.field);
        }
    }

    if (fieldErrors.length === 0) {
        return null;
    }

    return {
        summary: ['Complete all required binary feature mappings with unique columns.'],
        fieldErrors,
    };
}

function buildBinaryFeatureCreateRequest(args: {
    datasetName: string;
    uploadedFileName: string;
    setupState: BinaryFeatureAeSetupState;
}): ApiCreateDatasetConfigRequest {
    return {
        dataset_name: args.datasetName,
        performance_type: 'Binary Feature Mortality A/E',
        file_path: args.uploadedFileName,
        module_id: 'binary_feature_ae',
        module_config: {
            rule: args.setupState.rule ?? '',
            RuleName: args.setupState.RuleName ?? '',
            first_date: args.setupState.first_date ?? '',
            category: args.setupState.category ?? '',
            hit_count: args.setupState.hit_count ?? '',
            hit_rate: args.setupState.hit_rate ?? '',
            claim_count: args.setupState.claim_count ?? '',
            mec_sum: args.setupState.mec_sum ?? '',
            ae_ratio: args.setupState.ae_ratio ?? '',
            ci_lower_95: args.setupState.ci_lower_95 ?? '',
            ci_upper_95: args.setupState.ci_upper_95 ?? '',
            ci_lower_90: args.setupState.ci_lower_90 ?? '',
            ci_upper_90: args.setupState.ci_upper_90 ?? '',
            ci_lower_80: args.setupState.ci_lower_80 ?? '',
            ci_upper_80: args.setupState.ci_upper_80 ?? '',
            cola_cancer_pct: args.setupState.cola_cancer_pct ?? '',
            cola_heart_pct: args.setupState.cola_heart_pct ?? '',
            cola_nervous_system_pct: args.setupState.cola_nervous_system_pct ?? '',
            cola_non_natural_pct: args.setupState.cola_non_natural_pct ?? '',
            cola_other_medical_pct: args.setupState.cola_other_medical_pct ?? '',
            cola_respiratory_pct: args.setupState.cola_respiratory_pct ?? '',
            cola_others_pct: args.setupState.cola_others_pct ?? '',
        },
    };
}

function loadBinaryFeatureSetupStateFromConfig(
    config: ApiDatasetConfig,
): BinaryFeatureAeSetupState {
    if (!isBinaryFeatureDatasetConfig(config)) {
        return createInitialBinaryFeatureSetupState();
    }

    return {
        ...config.module_config,
    };
}

export const mortalityAeModule: AnalysisModuleDefinition<
    MortalityAeSetupState,
    ApiDatasetSchemaResults
> = {
    id: 'mortality_ae',
    label: 'Experience Study Mortality A/E',
    status: 'active',
    analysisRoute: '/mortality-ae/analysis',
    performanceType: 'Mortality A/E Analysis',
    setupComponent: () =>
        import('@/modules/mortality-ae/components/MortalityColumnMapper.vue'),
    createInitialSetupState: createInitialMortalitySetupState,
    validateSetupState: validateMortalitySetupState,
    buildCreateRequest: buildMortalityCreateRequest,
    loadSetupStateFromExistingConfig: loadMortalitySetupStateFromConfig,
    loadSetupContext: async (file: File) => postAeUploadSchema(file),
};

export const binaryFeatureAeModule: AnalysisModuleDefinition<
    BinaryFeatureAeSetupState
> = {
    id: 'binary_feature_ae',
    label: 'Binary Feature Mortality A/E',
    status: 'active',
    analysisRoute: '/binary-feature-ae/analysis',
    performanceType: 'Binary Feature Mortality A/E',
    setupComponent: () =>
        import('@/modules/binary-feature-ae/components/BinaryFeatureMapper.vue'),
    createInitialSetupState: createInitialBinaryFeatureSetupState,
    validateSetupState: validateBinaryFeatureSetupState,
    buildCreateRequest: buildBinaryFeatureCreateRequest,
    loadSetupStateFromExistingConfig: loadBinaryFeatureSetupStateFromConfig,
};

export const analysisModules: AnyAnalysisModuleDefinition[] = [
    mortalityAeModule,
    binaryFeatureAeModule,
];

export const activeAnalysisModules = analysisModules.filter(
    (module) => module.status === 'active',
);

export function getAnalysisModuleById(
    moduleId: ModuleId | null,
): AnyAnalysisModuleDefinition | null {
    if (!moduleId) {
        return null;
    }
    return analysisModules.find((module) => module.id === moduleId) ?? null;
}

export function getAnalysisModuleForConfig(
    config: ApiDatasetConfig,
): AnyAnalysisModuleDefinition | null {
    return getAnalysisModuleById(config.module_id);
}
