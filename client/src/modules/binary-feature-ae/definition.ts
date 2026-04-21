import type {
    ApiBinaryFeatureAeModuleConfig,
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
} from '@/types/dataset-config';
import { isBinaryFeatureDatasetConfig } from '@/types/dataset-config';

import type {
    AnalysisModuleDefinition,
    ModuleFieldError,
    ModuleValidationResult,
} from '@/core/registry';
import { BINARY_FEATURE_FIELD_DEFINITIONS } from '@/modules/binary-feature-ae/constants';

export type BinaryFeatureAeSetupState = {
    [K in keyof ApiBinaryFeatureAeModuleConfig]: string | null;
};

function createInitialBinaryFeatureSetupState(): BinaryFeatureAeSetupState {
    const state = {} as BinaryFeatureAeSetupState;
    for (const field of BINARY_FEATURE_FIELD_DEFINITIONS) {
        state[field.key] = null;
    }
    return state;
}

const requiredFields = BINARY_FEATURE_FIELD_DEFINITIONS.map((field) => field.key);

function validateBinaryFeatureSetupState(
    state: BinaryFeatureAeSetupState,
): ModuleValidationResult {
    const fieldErrors: ModuleFieldError[] = [];

    for (const field of requiredFields) {
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
    const moduleConfig = Object.fromEntries(
        BINARY_FEATURE_FIELD_DEFINITIONS.map((field) => [
            field.key,
            args.setupState[field.key] ?? '',
        ]),
    ) as unknown as ApiBinaryFeatureAeModuleConfig;

    return {
        dataset_name: args.datasetName,
        performance_type: 'Binary Feature Mortality A/E',
        file_path: args.uploadedFileName,
        module_id: 'binary_feature_ae',
        module_config: moduleConfig,
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

export const binaryFeatureAeModule: AnalysisModuleDefinition<BinaryFeatureAeSetupState> = {
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
