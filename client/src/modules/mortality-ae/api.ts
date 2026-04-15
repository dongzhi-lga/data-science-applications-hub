import {
    createSlicedUploadFile,
    postFormData,
    postJson,
} from '@/core/http';
import type { ApiDatasetSchemaResults } from '@/types/datasets';

import type {
    ApiAeInsightsResults,
    ApiAeUnivariateFromConfigParameters,
    ApiAeUnivariateParameters,
    ApiAeUnivariateResults,
} from './types';

export async function postAeUnivariate(
    params: ApiAeUnivariateParameters,
): Promise<ApiAeUnivariateResults> {
    return postJson<ApiAeUnivariateResults>('/api/ae/univariate', params);
}

export async function postAeUnivariateFromConfig(
    params: ApiAeUnivariateFromConfigParameters,
): Promise<ApiAeUnivariateResults> {
    return postJson<ApiAeUnivariateResults>(
        '/api/ae/univariate-from-config',
        params,
    );
}

export async function postAeUploadSchema(
    file: File,
): Promise<ApiDatasetSchemaResults> {
    const formData = new FormData();
    formData.append('file', createSlicedUploadFile(file));
    return postFormData<ApiDatasetSchemaResults>('/api/ae/upload-schema', formData);
}

export async function postAeUnivariateFromCsv(
    file: File,
    params: ApiAeUnivariateParameters,
): Promise<ApiAeUnivariateResults> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('params', JSON.stringify(params));

    return postFormData<ApiAeUnivariateResults>(
        '/api/ae/univariate-from-csv',
        formData,
    );
}

export async function getAeInsightsFromConfig(
    configId: string,
    maxResultsPerMetric = 25,
): Promise<ApiAeInsightsResults> {
    return postJson<ApiAeInsightsResults>('/api/ae/insights/from-config', {
        config_id: configId,
        max_results_per_metric: maxResultsPerMetric,
    });
}
