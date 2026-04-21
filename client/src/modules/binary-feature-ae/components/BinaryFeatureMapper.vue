<template>
    <q-card flat bordered class="q-mt-md">
        <q-card-section class="q-pb-sm">
            <div class="text-h6">Binary Feature Mortality A/E Mapping</div>
            <div class="text-body2 text-grey-7">
                Map the uploaded rule-stat columns to the canonical Binary Feature fields.
            </div>
        </q-card-section>

        <q-card-section v-if="schema" class="q-pt-none">
            <q-banner
                v-if="allFieldsMapped"
                class="bg-positive text-white q-mb-md"
                dense
                rounded
            >
                All required fields are mapped. Review any assignments below before saving.
            </q-banner>

            <div
                v-for="section in fieldSections"
                :key="section.title"
                class="q-mb-lg"
            >
                <div class="text-subtitle2 text-weight-medium q-mb-sm">
                    {{ section.title }}
                </div>
                <div class="row q-col-gutter-md">
                    <div
                        v-for="field in section.fields"
                        :key="field.key"
                        class="col-12 col-md-6"
                    >
                        <q-select
                            :model-value="setupState[field.key]"
                            :options="columnOptions"
                            emit-value
                            map-options
                            outlined
                            dense
                            options-dense
                            :label="`${field.label} *`"
                            :hint="field.sourceName"
                            :error="Boolean(errorsByField[field.key])"
                            :error-message="errorsByField[field.key]"
                            @update:model-value="updateField(field.key, $event)"
                        />
                    </div>
                </div>
            </div>
        </q-card-section>
    </q-card>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue';

import type { ModuleFieldError } from '@/core/registry';
import type { ApiCoreDatasetSchemaResults } from '@/core/types/schema';
import {
    BINARY_FEATURE_FIELD_DEFINITIONS,
    BINARY_FEATURE_FIELD_SECTIONS,
} from '@/modules/binary-feature-ae/constants';
import type { BinaryFeatureAeSetupState } from '@/modules/binary-feature-ae/definition';

const props = defineProps<{
    schema: ApiCoreDatasetSchemaResults | null;
    setupState: BinaryFeatureAeSetupState;
    setupErrors?: ModuleFieldError[] | null;
    setupContext?: unknown;
}>();

const emit = defineEmits<{
    'update:setupState': [value: BinaryFeatureAeSetupState];
}>();

const fieldDefinitions = BINARY_FEATURE_FIELD_DEFINITIONS;
const fieldSections = BINARY_FEATURE_FIELD_SECTIONS;

const errorsByField = computed<Record<string, string>>(() => {
    const next: Record<string, string> = {};
    for (const error of props.setupErrors ?? []) {
        next[error.field] = error.message;
    }
    return next;
});

const columnOptions = computed(() => {
    return (props.schema?.columns ?? []).map((column) => ({
        label: column.name,
        value: column.name,
    }));
});

const allFieldsMapped = computed(() => {
    return fieldDefinitions.every((field) => Boolean(props.setupState[field.key]));
});

function normalizeColumnName(value: string): string {
    return String(value || '')
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '');
}

function hasAnySetupValue(state: BinaryFeatureAeSetupState): boolean {
    return Object.values(state).some((value) => Boolean(value));
}

function updateField(
    field: keyof BinaryFeatureAeSetupState,
    value: string | null,
) {
    emit('update:setupState', {
        ...props.setupState,
        [field]: value,
    });
}

watch(
    () => props.schema,
    (schema) => {
        if (!schema || hasAnySetupValue(props.setupState)) {
            return;
        }

        const availableColumns = schema.columns.map((column) => column.name);
        const unusedColumns = new Set(availableColumns);
        const nextState: BinaryFeatureAeSetupState = { ...props.setupState };

        for (const field of fieldDefinitions) {
            const exactMatches = availableColumns.filter(
                (column) => column === field.sourceName || column === field.key,
            );
            const normalizedMatches = availableColumns.filter(
                (column) =>
                    normalizeColumnName(column) === normalizeColumnName(field.sourceName) ||
                    normalizeColumnName(column) === normalizeColumnName(field.key),
            );
            const candidates = exactMatches.length > 0 ? exactMatches : normalizedMatches;
            const uniqueCandidates = [...new Set(candidates)].filter((column) =>
                unusedColumns.has(column),
            );

            if (uniqueCandidates.length === 1) {
                nextState[field.key] = uniqueCandidates[0];
                unusedColumns.delete(uniqueCandidates[0]);
            }
        }

        emit('update:setupState', nextState);
    },
    { immediate: true },
);
</script>
