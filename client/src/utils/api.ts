import type {
    ApiMonitorFromCsvParameters,
    ApiMonitorFromCsvResults,
    ApiMonitorFromDatasetParameters,
} from '@/types/monitor';
import {
    createSlicedUploadFile,
    deleteRequest,
    fetchApi,
    getJson,
    postFormData,
    postJson,
} from '@/core/http';
import type {
    ApiDatasetColaResults,
    ApiDatasetSchemaResults,
    ApiListDatasetsResults,
} from '@/types/datasets';
import type { ApiCoreDatasetSchemaResults } from '@/core/types/schema';

export async function getDatasets(): Promise<ApiListDatasetsResults> {
    return getJson<ApiListDatasetsResults>('/api/datasets');
}

export async function getDatasetSchema(
    datasetName: string,
): Promise<ApiDatasetSchemaResults> {
    return getJson<ApiDatasetSchemaResults>(
        `/api/datasets/${encodeURIComponent(datasetName)}/schema`,
    );
}

export async function getDatasetCola(
    datasetName: string,
): Promise<ApiDatasetColaResults> {
    return getJson<ApiDatasetColaResults>(
        `/api/datasets/${encodeURIComponent(datasetName)}/cola`,
    );
}

export async function postMonitorFromCsv(
    file: File,
    params: ApiMonitorFromCsvParameters,
): Promise<ApiMonitorFromCsvResults> {
    const form = new FormData();
    form.append('file', file);
    form.append('params', JSON.stringify(params ?? {}));

    return postFormData<ApiMonitorFromCsvResults>('/api/monitor/from-csv', form);
}

export async function postMonitorFromDataset(
    params: ApiMonitorFromDatasetParameters,
): Promise<ApiMonitorFromCsvResults> {
    return postJson<ApiMonitorFromCsvResults>('/api/monitor/from-dataset', params);
}

export async function postCoreUploadSchema(
    file: File,
): Promise<ApiCoreDatasetSchemaResults> {
    const form = new FormData();
    form.append('file', createSlicedUploadFile(file));
    return postFormData<ApiCoreDatasetSchemaResults>('/api/core/upload-schema', form);
}

// Dataset Config API
import type {
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
    ApiListDatasetConfigsResults,
} from '@/types/dataset-config';
import type {
    ApiBinaryFeatureCalculateRequest,
    ApiBinaryFeatureCalculateResponse,
} from '@/types/binary-feature-ae';

export async function getDatasetConfigs(): Promise<ApiListDatasetConfigsResults> {
    return getJson<ApiListDatasetConfigsResults>('/api/dataset-configs');
}

export async function createDatasetConfig(
    request: ApiCreateDatasetConfigRequest,
    file: File,
): Promise<ApiDatasetConfig> {
    const formData = new FormData();
    formData.append('dataset_name', request.dataset_name);
    formData.append('performance_type', request.performance_type);
    formData.append('module_id', request.module_id);
    formData.append('module_config_json', JSON.stringify(request.module_config));
    formData.append('file', file);

    return postFormData<ApiDatasetConfig>('/api/dataset-configs', formData);
}

export async function getDatasetConfig(configId: string): Promise<ApiDatasetConfig> {
    return getJson<ApiDatasetConfig>(
        `/api/dataset-configs/${encodeURIComponent(configId)}`,
    );
}

export async function getDatasetConfigSchema(
    configId: string,
): Promise<ApiDatasetSchemaResults> {
    return getJson<ApiDatasetSchemaResults>(
        `/api/dataset-configs/${encodeURIComponent(configId)}/schema`,
    );
}

export async function deleteDatasetConfig(configId: string): Promise<void> {
    await deleteRequest(`/api/dataset-configs/${encodeURIComponent(configId)}`);
}

export async function getDatasetConfigFile(configId: string): Promise<File> {
    // First get the config to extract the original filename as fallback
    const config = await getDatasetConfig(configId);
    const fallbackFilename = config.file_path;
    
    const res = await fetchApi(
        `/api/dataset-configs/${encodeURIComponent(configId)}/file`,
    );

    const blob = await res.blob();
    const contentDisposition = res.headers.get('content-disposition');
    let filename = fallbackFilename; // Use fallback by default
    
    if (contentDisposition) {
        // Try multiple patterns for extracting filename
        const patterns = [
            /filename[*]?=["']?([^"'\n;]+)["']?/i,
            /filename="([^"]+)"/i,
            /filename='([^']+)'/i,
            /filename=([^;\n]+)/i,
        ];
        
        for (const pattern of patterns) {
            const match = pattern.exec(contentDisposition);
            if (match && match[1]) {
                filename = match[1].trim();
                console.log('Extracted filename from content-disposition:', filename);
                break;
            }
        }
    }
    
    console.log('Using filename:', filename, 'for File object');
    
    // Infer MIME type from extension
    const getMimeType = (fname: string): string => {
        const ext = fname.toLowerCase().split('.').pop();
        switch (ext) {
            case 'csv': return 'text/csv';
            case 'xlsx': return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
            case 'xls': return 'application/vnd.ms-excel';
            case 'parquet': return 'application/octet-stream';
            default: return blob.type || 'application/octet-stream';
        }
    };
    
    return new File([blob], filename, { type: getMimeType(filename) });
}

export async function postBinaryFeatureCalculate(
    params: ApiBinaryFeatureCalculateRequest,
): Promise<ApiBinaryFeatureCalculateResponse> {
    return postJson<ApiBinaryFeatureCalculateResponse>(
        '/api/binary-feature-ae/calculate',
        params,
    );
}
