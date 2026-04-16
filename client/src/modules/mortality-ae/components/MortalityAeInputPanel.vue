<template>
    <div>
        <q-banner class="q-px-md q-pt-md q-pb-sm">
            <div class="row items-center q-gutter-x-sm">
                <span class="text-h4">Experience Study Mortality A/E</span>
            </div>
            <div class="text-body2 text-grey-7 q-mt-xs">
                Load a saved mortality configuration and run the Experience Study
                Mortality A/E workflow.
            </div>
        </q-banner>

        <q-card class="q-mt-md">
            <q-expansion-item
                switch-toggle-side
                label="About"
                header-class="text-primary"
            >
                <div class="q-pa-md">
                    This tool runs locally and analyzes uploaded data files (CSV, Excel,
                    Parquet). It computes A/E (Actual vs Expected) ratios across x-axis
                    groups and can optionally overlay split results on the same chart.
                </div>
            </q-expansion-item>
        </q-card>

        <q-card class="q-pa-md q-mt-md">
            <q-banner class="q-pa-sm">
                <span class="text-h5">Inputs</span>
            </q-banner>

            <form class="q-mt-sm" @submit.prevent="handlers.onAnalyze">
                <div class="row items-center q-col-gutter-md q-mb-md">
                    <div class="col-12">
                        <q-select
                            v-model="model.selectedConfigId"
                            :options="model.configOptions"
                            emit-value
                            map-options
                            outlined
                            dense
                            label="Select Saved Dataset Configuration"
                            class="input-600"
                            clearable
                            :loading="model.configsLoading"
                            hint="Choose a previously configured dataset from the Data Input page"
                        >
                            <template #prepend>
                                <q-icon name="folder_open" />
                            </template>
                        </q-select>
                    </div>
                </div>

                <div v-if="model.selectedConfig" class="q-mb-md">
                    <q-banner class="bg-green-1" dense>
                        <template #avatar>
                            <q-icon name="check_circle" color="positive" />
                        </template>
                        <strong>{{ model.selectedConfig.dataset_name }}</strong> loaded
                        successfully
                        <br />File and column mappings loaded automatically from saved
                        configuration
                    </q-banner>
                </div>

                <div v-if="!model.selectedConfig" class="q-mb-md">
                    <q-banner class="bg-grey-3" dense>
                        <template #avatar>
                            <q-icon name="info" color="grey-7" />
                        </template>
                        Please select a saved dataset configuration above, or go to the
                        <strong>Central Setup</strong> page to create a new one.
                    </q-banner>
                </div>

                <AeInsightBanner
                    v-if="model.selectedConfig"
                    class="q-mb-md"
                    :insights="model.insightResults"
                    :loading="model.insightsLoading"
                    :error="model.insightsError"
                    @apply="handlers.applyInsightDrill"
                />

                <MortalityAeVariableControls :model="model" class="q-mt-md" />

                <q-card v-if="model.polyFitEligible" flat bordered class="q-mt-md">
                    <q-card-section class="q-pb-sm">
                        <div class="text-h6">Polynomial Best Fit (optional)</div>
                        <div class="text-body2 text-grey-7">
                            Optionally configure a simple polynomial best-fit for the plotted
                            relationship.
                        </div>
                    </q-card-section>

                    <q-card-section class="q-pt-none">
                        <div class="row items-center q-gutter-md">
                            <q-checkbox
                                v-model="model.polyEnabled"
                                dense
                                label="Enable polynomial fit"
                            />
                            <q-select
                                v-model="model.polyDegree"
                                :options="model.polyDegreeOptions"
                                outlined
                                dense
                                options-dense
                                emit-value
                                map-options
                                label="Degree"
                                class="poly-input"
                                :disable="!model.polyEnabled"
                            />
                            <q-checkbox
                                v-model="model.polyWeighted"
                                dense
                                label="Weighted fit"
                                :disable="!model.polyEnabled"
                            />
                        </div>
                    </q-card-section>
                </q-card>

                <div class="row items-center q-gutter-sm q-mt-md">
                    <q-btn
                        label="Analyze"
                        type="submit"
                        color="primary"
                        :disable="!model.canAnalyze || model.loading"
                        :loading="model.loading"
                    />
                    <div v-if="model.errorMsg" class="text-negative">
                        {{ model.errorMsg }}
                    </div>
                </div>
            </form>
        </q-card>
    </div>
</template>

<script setup lang="ts">
import AeInsightBanner from './AeInsightBanner.vue';
import MortalityAeVariableControls from './MortalityAeVariableControls.vue';

defineProps<{
    model: Record<string, any>;
    handlers: Record<string, any>;
}>();
</script>

<style scoped>
.input-600 {
    width: 600px;
    max-width: 100%;
}

.poly-input {
    width: 200px;
    max-width: 100%;
}
</style>
