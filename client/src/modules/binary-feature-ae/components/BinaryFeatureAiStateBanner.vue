<template>
    <div
        v-if="isStale || sourceMode === 'fallback' || usedReferenceContext"
        class="q-mb-sm"
    >
        <q-banner
            v-if="isStale"
            class="bg-amber-1 text-amber-10 q-mb-sm"
            rounded
            dense
        >
            <template #avatar>
                <q-icon name="update" color="amber-10" />
            </template>
            This AI response may be stale because the current view changed after it was generated.
            Re-run the AI action for the latest filters, perspective, or selected rule.
        </q-banner>

        <q-banner
            v-if="sourceMode === 'fallback'"
            class="bg-orange-1 text-orange-10 q-mb-sm"
            rounded
            dense
        >
            <template #avatar>
                <q-icon name="shield" color="orange-10" />
            </template>
            Deterministic fallback explanation shown. This response uses uploaded rule metrics and current view state only.
            <div v-if="validationNotes.length" class="text-caption q-mt-xs">
                {{ validationNotes[0] }}
            </div>
        </q-banner>

        <q-banner
            v-if="usedReferenceContext"
            class="bg-blue-1 text-blue-10 q-mb-sm"
            rounded
            dense
        >
            <template #avatar>
                <q-icon name="menu_book" color="blue-10" />
            </template>
            Reference context was used to help explain rule meaning.
            <span v-if="referenceSources.length">
                Sources: {{ referenceSources.join(', ') }}
            </span>
        </q-banner>
    </div>
</template>

<script setup lang="ts">
import type { BinaryFeatureAiSourceMode } from '@/types/binary-feature-ae';

defineProps<{
    isStale: boolean;
    sourceMode: BinaryFeatureAiSourceMode | null;
    usedReferenceContext: boolean;
    referenceSources: string[];
    validationNotes: string[];
}>();
</script>
