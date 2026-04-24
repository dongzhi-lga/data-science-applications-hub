import { computed, onBeforeUnmount, ref, type Ref } from 'vue';

import { postBinaryFeatureAiExplainFocusedRule } from '@/modules/binary-feature-ae/api';
import type {
    ApiBinaryFeatureAiResponse,
    ApiBinaryFeatureRow,
    BinaryFeatureCiLevel,
    BinaryFeaturePerspective,
    BinaryFeatureSignificance,
} from '@/types/binary-feature-ae';
import type { ApiDatasetConfig } from '@/types/dataset-config';

interface UseBinaryFeatureAiOptions {
    activeConfig: Readonly<Ref<ApiDatasetConfig | null>>;
    focusedRow: Readonly<Ref<ApiBinaryFeatureRow | null>>;
    responseStateFingerprint: Readonly<Ref<string | null | undefined>>;
    perspective: Readonly<Ref<BinaryFeaturePerspective>>;
    ciLevel: Readonly<Ref<BinaryFeatureCiLevel>>;
    categories: Readonly<Ref<string[]>>;
    significanceValues: Readonly<Ref<BinaryFeatureSignificance[]>>;
    searchText: Readonly<Ref<string>>;
    minHitCount: Readonly<Ref<number | null>>;
    minClaimCount: Readonly<Ref<number | null>>;
}

export function useBinaryFeatureAi(options: UseBinaryFeatureAiOptions) {
    const aiExplainLoading = ref(false);
    const aiExplainError = ref<string | null>(null);
    const aiExplainResponse = ref<ApiBinaryFeatureAiResponse | null>(null);

    let explainAbortController: AbortController | null = null;

    const isAiExplainStale = computed(() => {
        if (!aiExplainResponse.value || !options.responseStateFingerprint.value) {
            return false;
        }

        return (
            aiExplainResponse.value.state_fingerprint !==
            options.responseStateFingerprint.value
        );
    });

    function clearExplainState() {
        explainAbortController?.abort();
        explainAbortController = null;
        aiExplainLoading.value = false;
        aiExplainError.value = null;
        aiExplainResponse.value = null;
    }

    async function explainFocusedRule() {
        if (!options.activeConfig.value || !options.focusedRow.value) {
            return;
        }

        const explainedRowId = options.focusedRow.value.row_id;
        clearExplainState();

        explainAbortController = new AbortController();
        const signal = explainAbortController.signal;
        aiExplainLoading.value = true;

        try {
            aiExplainResponse.value = await postBinaryFeatureAiExplainFocusedRule(
                {
                    config_id: options.activeConfig.value.id,
                    perspective: options.perspective.value,
                    ci_level: options.ciLevel.value,
                    categories: options.categories.value,
                    significance_values: options.significanceValues.value,
                    search_text: options.searchText.value || null,
                    min_hit_count: options.minHitCount.value,
                    min_claim_count: options.minClaimCount.value,
                    row_id: explainedRowId,
                },
                signal,
            );
        } catch (err) {
            if (signal.aborted) {
                return;
            }

            const message = err instanceof Error ? err.message : String(err);
            aiExplainError.value =
                message === 'Not Found'
                    ? 'Explain Focused Rule endpoint was not found on the backend. Restart the FastAPI server on port 8000 so it loads the /api/binary-feature-ae/ai/explain-focused-rule route.'
                    : message;
        } finally {
            if (!signal.aborted) {
                aiExplainLoading.value = false;
            }
        }
    }

    onBeforeUnmount(() => {
        clearExplainState();
    });

    return {
        aiExplainLoading,
        aiExplainError,
        aiExplainResponse,
        isAiExplainStale,
        clearExplainState,
        explainFocusedRule,
    };
}
