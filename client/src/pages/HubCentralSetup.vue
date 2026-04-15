<template>
    <q-page class="q-pa-md">
        <div class="main-container">
            <q-banner class="q-px-md q-pt-md q-pb-sm">
                <div class="row items-center q-gutter-x-sm">
                    <span class="text-h4">Data Science Applications Hub</span>
                </div>
                <div class="text-body2 text-grey-7 q-mt-xs">
                    Select an analysis module, upload a dataset, configure module-specific
                    options, and launch the analysis workflow.
                </div>
            </q-banner>

            <q-card class="q-pa-md q-mt-md">
                <q-banner class="q-pa-sm">
                    <span class="text-h5">Central Setup</span>
                </q-banner>

                <form class="q-mt-sm" @submit.prevent="onSaveConfig">
                    <div class="row items-center q-col-gutter-md q-mb-md">
                        <div class="col-12 col-md-6">
                            <q-select
                                v-model="selectedModuleId"
                                :options="moduleOptions"
                                emit-value
                                map-options
                                outlined
                                dense
                                label="Task / Module Select"
                                class="input-400"
                                :disable="moduleOptions.length <= 1"
                            />
                        </div>
                    </div>

                    <div class="row items-center q-col-gutter-md q-mb-md">
                        <div class="col-12 col-md-6">
                            <q-file
                                v-model="uploadedFile"
                                outlined
                                dense
                                accept=".csv,.xlsx,.xls,.parquet"
                                label="Upload Data File"
                                clearable
                            >
                                <template #prepend>
                                    <q-icon name="attach_file" />
                                </template>
                            </q-file>
                        </div>
                        <div class="col-auto">
                            <q-btn
                                label="Load Schema"
                                color="primary"
                                dense
                                unelevated
                                :disable="!uploadedFile || !activeModule"
                                :loading="schemaLoading"
                                @click="onLoadUploadedSchema"
                            />
                        </div>
                        <div v-if="schemaSummary" class="col-12">
                            <div class="text-body2 text-grey-8">
                                Columns: {{ schemaSummary.total }} (numeric:
                                {{ schemaSummary.numeric }}, date:
                                {{ schemaSummary.date }}, categorical:
                                {{ schemaSummary.categorical }})
                            </div>
                        </div>
                    </div>

                    <component
                        :is="activeSetupComponent"
                        v-if="activeSetupComponent"
                        v-model:setupState="setupState"
                        :schema="schema"
                        :setup-context="setupContext"
                        :setup-errors="fieldErrors"
                    />

                    <div v-if="schema" class="row items-center q-col-gutter-md q-mt-md">
                        <div class="col-12 col-md-6">
                            <q-input
                                v-model="datasetName"
                                outlined
                                dense
                                label="Dataset Name *"
                                hint="Friendly name for this configuration"
                                :error="showValidation && !datasetName.trim()"
                                error-message="Required"
                            />
                        </div>
                        <div class="col-12 col-md-6 row items-center q-gutter-md">
                            <q-btn
                                type="submit"
                                label="Save Configuration"
                                color="primary"
                                unelevated
                                :loading="saving"
                                :disable="!activeModule || !uploadedFile || !schema"
                            />
                            <q-btn
                                label="Clear"
                                color="grey-7"
                                flat
                                @click="onClear"
                            />
                        </div>
                    </div>

                    <div v-if="validationMessages.length" class="q-mt-md">
                        <q-banner class="bg-negative text-white" dense>
                            <div v-for="message in validationMessages" :key="message">
                                {{ message }}
                            </div>
                        </q-banner>
                    </div>

                    <div v-if="errorMsg" class="q-mt-md">
                        <q-banner class="bg-negative text-white" dense>
                            {{ errorMsg }}
                        </q-banner>
                    </div>
                </form>
            </q-card>

            <q-card class="q-pa-md q-mt-md">
                <q-banner class="q-pa-sm">
                    <span class="text-h5">Saved Configurations</span>
                </q-banner>

                <div class="q-mt-md">
                    <q-table
                        :rows="configs"
                        :columns="libraryColumns"
                        row-key="id"
                        flat
                        :loading="configsLoading"
                        :pagination="{ rowsPerPage: 10 }"
                    >
                        <template #body-cell-performance_type="props">
                            <q-td :props="props">
                                {{ getConfigModuleLabel(props.row) }}
                            </q-td>
                        </template>
                        <template #body-cell-actions="props">
                            <q-td :props="props">
                                <q-btn
                                    label="Open Analysis"
                                    color="primary"
                                    size="sm"
                                    flat
                                    dense
                                    @click="onOpenAnalysis(props.row)"
                                />
                                <q-btn
                                    icon="delete"
                                    color="negative"
                                    size="sm"
                                    flat
                                    dense
                                    @click="onDeleteConfig(props.row)"
                                />
                            </q-td>
                        </template>
                        <template #body-cell-created_date="props">
                            <q-td :props="props">
                                {{ formatDate(props.row.created_date) }}
                            </q-td>
                        </template>
                    </q-table>
                </div>
            </q-card>
        </div>
    </q-page>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';

import type { AnyAnalysisModuleDefinition } from '@/core/registry';
import {
    activeAnalysisModules,
    getAnalysisModuleById,
    getAnalysisModuleForConfig,
} from '@/core/registry';
import type { ApiCoreDatasetSchemaResults } from '@/core/types/schema';
import type { ApiDatasetConfig } from '@/types/dataset-config';
import {
    createDatasetConfig,
    deleteDatasetConfig,
    getDatasetConfigs,
    postCoreUploadSchema,
} from '@/utils/api';

const router = useRouter();
const $q = useQuasar();

const selectedModuleId = ref(activeAnalysisModules[0]?.id ?? null);
const uploadedFile = ref<File | null>(null);
const schema = ref<ApiCoreDatasetSchemaResults | null>(null);
const setupContext = ref<unknown | null>(null);
const setupState = ref<unknown>(null);
const schemaLoading = ref(false);
const saving = ref(false);
const errorMsg = ref<string | null>(null);
const showValidation = ref(false);
const datasetName = ref('');
const configs = ref<ApiDatasetConfig[]>([]);
const configsLoading = ref(false);

const activeModule = computed<AnyAnalysisModuleDefinition | null>(() => {
    return getAnalysisModuleById(selectedModuleId.value);
});

const moduleOptions = computed(() => {
    return activeAnalysisModules.map((module) => ({
        label: module.label,
        value: module.id,
    }));
});

const activeSetupComponent = computed(() => {
    if (!activeModule.value) {
        return null;
    }
    return defineAsyncComponent(activeModule.value.setupComponent);
});

const moduleValidationResult = computed(() => {
    if (!activeModule.value || setupState.value === null) {
        return null;
    }
    return activeModule.value.validateSetupState(setupState.value);
});

const fieldErrors = computed(() => {
    if (!showValidation.value) {
        return [];
    }
    return moduleValidationResult.value?.fieldErrors ?? [];
});

const validationMessages = computed(() => {
    if (!showValidation.value) {
        return [];
    }

    const messages: string[] = [];
    if (!activeModule.value) {
        messages.push('Select an analysis module.');
    }
    if (!uploadedFile.value) {
        messages.push('Upload a data file.');
    }
    if (!schema.value) {
        messages.push('Load schema before saving.');
    }
    if (!datasetName.value.trim()) {
        messages.push('Dataset name is required.');
    }
    messages.push(...(moduleValidationResult.value?.summary ?? []));
    return messages;
});

const schemaSummary = computed(() => {
    if (!schema.value) return null;
    const numeric = schema.value.columns.filter((column) => column.kind === 'numeric').length;
    const date = schema.value.columns.filter((column) => column.kind === 'date').length;
    const categorical = schema.value.columns.filter(
        (column) => column.kind === 'categorical',
    ).length;
    return {
        total: schema.value.columns.length,
        numeric,
        date,
        categorical,
    };
});

const libraryColumns = [
    {
        name: 'dataset_name',
        label: 'Dataset Name',
        field: 'dataset_name',
        align: 'left' as const,
        sortable: true,
    },
    {
        name: 'performance_type',
        label: 'Module',
        field: 'performance_type',
        align: 'left' as const,
        sortable: true,
    },
    {
        name: 'file_path',
        label: 'File',
        field: 'file_path',
        align: 'left' as const,
        sortable: true,
        format: (val: string) => val.split(/[/\\]/).pop() || val,
    },
    {
        name: 'created_date',
        label: 'Created',
        field: 'created_date',
        align: 'left' as const,
        sortable: true,
    },
    {
        name: 'actions',
        label: 'Actions',
        field: 'id',
        align: 'center' as const,
    },
];

function resetSetupState() {
    setupState.value = activeModule.value?.createInitialSetupState() ?? null;
    setupContext.value = null;
    schema.value = null;
    showValidation.value = false;
}

async function onLoadUploadedSchema() {
    if (!uploadedFile.value || !activeModule.value) {
        return;
    }

    schemaLoading.value = true;
    errorMsg.value = null;
    schema.value = null;
    setupContext.value = null;
    showValidation.value = false;

    try {
        schema.value = await postCoreUploadSchema(uploadedFile.value);
        if (activeModule.value.loadSetupContext) {
            setupContext.value = await activeModule.value.loadSetupContext(
                uploadedFile.value,
                schema.value,
            );
        }

        if (!datasetName.value) {
            const filename = uploadedFile.value.name;
            datasetName.value = filename.replace(/\.(csv|xlsx?|parquet)$/i, '');
        }
    } catch (err) {
        errorMsg.value = err instanceof Error ? err.message : String(err);
    } finally {
        schemaLoading.value = false;
    }
}

async function onSaveConfig() {
    showValidation.value = true;
    errorMsg.value = null;

    if (validationMessages.value.length > 0 || !activeModule.value || !uploadedFile.value) {
        return;
    }

    saving.value = true;
    try {
        const request = activeModule.value.buildCreateRequest({
            datasetName: datasetName.value.trim(),
            uploadedFileName: uploadedFile.value.name,
            setupState: setupState.value,
        });
        const savedConfig = await createDatasetConfig(request, uploadedFile.value);
        $q.notify({
            type: 'positive',
            message: `${activeModule.value.label} configuration saved successfully`,
            position: 'top',
            timeout: 5000,
            actions: [
                {
                    label: 'Open Analysis',
                    color: 'white',
                    handler: () => {
                        router.push(
                            `${activeModule.value?.analysisRoute}?config=${savedConfig.id}`,
                        );
                    },
                },
            ],
        });
        await loadConfigs();
        onClear();
    } catch (err) {
        errorMsg.value = err instanceof Error ? err.message : String(err);
    } finally {
        saving.value = false;
    }
}

function onClear() {
    uploadedFile.value = null;
    datasetName.value = '';
    errorMsg.value = null;
    resetSetupState();
}

async function loadConfigs() {
    configsLoading.value = true;
    try {
        const result = await getDatasetConfigs();
        configs.value = result.configs;
    } catch (err) {
        $q.notify({
            type: 'negative',
            message: err instanceof Error ? err.message : 'Failed to load configurations',
            position: 'top',
        });
    } finally {
        configsLoading.value = false;
    }
}

function getConfigModuleLabel(config: ApiDatasetConfig): string {
    return getAnalysisModuleForConfig(config)?.label ?? config.performance_type;
}

function onOpenAnalysis(config: ApiDatasetConfig) {
    const module = getAnalysisModuleForConfig(config) ?? activeModule.value;
    if (!module) {
        return;
    }
    router.push(`${module.analysisRoute}?config=${config.id}`);
}

async function onDeleteConfig(config: ApiDatasetConfig) {
    $q.dialog({
        title: 'Confirm Delete',
        message: `Are you sure you want to delete "${config.dataset_name}"?`,
        cancel: true,
        persistent: true,
    }).onOk(async () => {
        try {
            await deleteDatasetConfig(config.id);
            $q.notify({
                type: 'positive',
                message: 'Configuration deleted',
                position: 'top',
            });
            await loadConfigs();
        } catch (err) {
            $q.notify({
                type: 'negative',
                message:
                    err instanceof Error
                        ? err.message
                        : 'Failed to delete configuration',
                position: 'top',
            });
        }
    });
}

function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleString();
}

watch(
    () => selectedModuleId.value,
    () => {
        errorMsg.value = null;
        resetSetupState();
    },
    { immediate: true },
);

watch(
    () => uploadedFile.value,
    () => {
        errorMsg.value = null;
        schema.value = null;
        setupContext.value = null;
        showValidation.value = false;
        if (activeModule.value) {
            setupState.value = activeModule.value.createInitialSetupState();
        }
    },
);

onMounted(() => {
    loadConfigs();
});
</script>

<style scoped>
.main-container {
    max-width: 1400px;
}

.input-400 {
    width: 400px;
}
</style>
