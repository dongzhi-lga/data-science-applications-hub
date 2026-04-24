<template>
    <div v-if="evidenceRefs.length">
        <div class="text-subtitle2 q-mb-xs">Evidence</div>
        <div class="row q-gutter-xs">
            <q-chip
                v-for="evidence in evidenceRefs"
                :key="`${evidence.row_id}-${evidence.reason_type}-${evidence.reason_label}`"
                clickable
                outline
                dense
                :color="severityColor(evidence.severity)"
                :icon="reasonIcon(evidence.reason_type)"
                @click="emit('focus-row', evidence.row_id)"
            >
                {{ evidence.reason_label }}
                <q-tooltip>
                    {{ evidence.rule_label }}
                </q-tooltip>
            </q-chip>
        </div>
    </div>
</template>

<script setup lang="ts">
import type {
    ApiBinaryFeatureAiEvidenceRef,
    BinaryFeatureAiReasonType,
    BinaryFeatureAiSeverity,
} from '@/types/binary-feature-ae';

defineProps<{
    evidenceRefs: ApiBinaryFeatureAiEvidenceRef[];
}>();

const emit = defineEmits<{
    'focus-row': [rowId: string];
}>();

function severityColor(severity: BinaryFeatureAiSeverity) {
    switch (severity) {
        case 'high':
            return 'negative';
        case 'medium':
            return 'orange-8';
        case 'low':
            return 'blue-grey-6';
        case 'neutral':
        default:
            return 'grey-7';
    }
}

function reasonIcon(reasonType: BinaryFeatureAiReasonType) {
    switch (reasonType) {
        case 'elevated_relative_to_expected':
            return 'trending_up';
        case 'below_expected':
            return 'trending_down';
        case 'uncertain_interval':
        case 'wide_uncertainty':
            return 'error_outline';
        case 'high_materiality':
            return 'priority_high';
        case 'count_amount_divergence':
            return 'compare_arrows';
        case 'reference_context_used':
            return 'menu_book';
        case 'selected_for_comparison':
            return 'checklist';
        case 'visible_pattern':
            return 'visibility';
        case 'focused_rule':
        default:
            return 'gps_fixed';
    }
}
</script>
