<template>
    <q-card flat bordered>
        <q-card-section class="row items-start justify-between q-col-gutter-md">
            <div class="col">
                <div class="text-h6">AI Explain Rule</div>
                <div v-if="focusedRow" class="text-caption text-grey-7">
                    {{ focusedRow.rule }} | {{ focusedRow.RuleName }}
                </div>
                <div v-else class="text-caption text-grey-7">
                    Select a rule from the scatter or the table.
                </div>
            </div>
            <div class="col-auto">
                <q-btn
                    label="Explain Rule"
                    color="primary"
                    unelevated
                    dense
                    :disable="!focusedRow || loading"
                    :loading="loading"
                    @click="emit('explain')"
                />
            </div>
        </q-card-section>

        <q-banner v-if="error" class="bg-negative text-white q-ma-md" rounded>
            {{ error }}
        </q-banner>

        <q-card-section v-else-if="result" class="q-pt-none">
            <div class="row items-center q-gutter-sm q-mb-sm">
                <q-badge color="primary" outline>
                    {{ sourceLabel }}
                </q-badge>
            </div>

            <div class="text-body2">
                {{ result.summary_text }}
            </div>

            <div v-if="result.key_findings.length" class="q-mt-md">
                <div class="text-subtitle2">Key Findings</div>
                <ul class="ai-list">
                    <li v-for="item in result.key_findings" :key="`finding-${item}`">
                        {{ item }}
                    </li>
                </ul>
            </div>

            <div v-if="result.caution_flags.length" class="q-mt-md">
                <div class="text-subtitle2">Cautions</div>
                <ul class="ai-list">
                    <li v-for="item in result.caution_flags" :key="`caution-${item}`">
                        {{ item }}
                    </li>
                </ul>
            </div>

            <div v-if="result.next_review_steps.length" class="q-mt-md">
                <div class="text-subtitle2">Next Review Steps</div>
                <ul class="ai-list">
                    <li v-for="item in result.next_review_steps" :key="`step-${item}`">
                        {{ item }}
                    </li>
                </ul>
            </div>
        </q-card-section>

        <q-card-section
            v-else
            class="text-body2 text-grey-7 q-pt-none"
        >
            Click Explain Rule to generate a focused explanation for the selected
            rule. If no LLM is configured, the module returns the deterministic
            fallback explanation.
        </q-card-section>
    </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import type {
    ApiBinaryFeatureAiResponse,
    ApiBinaryFeatureRow,
} from '@/types/binary-feature-ae';

const props = defineProps<{
    focusedRow: ApiBinaryFeatureRow | null;
    result: ApiBinaryFeatureAiResponse | null;
    loading: boolean;
    error: string | null;
}>();

const emit = defineEmits<{
    explain: [];
}>();

const sourceLabel = computed(() => {
    if (!props.result) {
        return '';
    }
    return props.result.source_mode === 'llm' ? 'LLM' : 'Fallback';
});
</script>

<style scoped>
.ai-list {
    margin: 8px 0 0;
    padding-left: 18px;
}

.ai-list li + li {
    margin-top: 6px;
}
</style>
