import { postJson } from '@/core/http';
import type {
    ApiBinaryFeatureAiExplainRuleRequest,
    ApiBinaryFeatureAiResponse,
    ApiBinaryFeatureCalculateRequest,
    ApiBinaryFeatureCalculateResponse,
} from '@/types/binary-feature-ae';

export async function postBinaryFeatureCalculate(
    params: ApiBinaryFeatureCalculateRequest,
    signal?: AbortSignal,
): Promise<ApiBinaryFeatureCalculateResponse> {
    return postJson<ApiBinaryFeatureCalculateResponse>(
        '/api/binary-feature-ae/calculate',
        params,
        signal,
    );
}

export async function postBinaryFeatureExplainRule(
    params: ApiBinaryFeatureAiExplainRuleRequest,
    signal?: AbortSignal,
): Promise<ApiBinaryFeatureAiResponse> {
    return postJson<ApiBinaryFeatureAiResponse>(
        '/api/binary-feature-ae/ai/explain-rule',
        params,
        signal,
    );
}
