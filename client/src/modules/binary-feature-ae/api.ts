import { postJson } from '@/core/http';
import type {
    ApiBinaryFeatureAiExplainFocusedRuleRequest,
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

export async function postBinaryFeatureAiExplainFocusedRule(
    params: ApiBinaryFeatureAiExplainFocusedRuleRequest,
    signal?: AbortSignal,
): Promise<ApiBinaryFeatureAiResponse> {
    return postJson<ApiBinaryFeatureAiResponse>(
        '/api/binary-feature-ae/ai/explain-focused-rule',
        params,
        signal,
    );
}

export async function postBinaryFeatureExplainRule(
    params: ApiBinaryFeatureAiExplainRuleRequest,
    signal?: AbortSignal,
): Promise<ApiBinaryFeatureAiResponse> {
    return postBinaryFeatureAiExplainFocusedRule(params, signal);
}
