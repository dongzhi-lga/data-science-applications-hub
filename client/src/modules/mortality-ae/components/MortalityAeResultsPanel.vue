<template>
    <div class="q-mt-lg">
        <q-banner class="q-px-md q-pt-md q-pb-sm">
            <div class="row items-center q-gutter-x-sm">
                <span class="text-h4">Results</span>
            </div>
        </q-banner>

        <q-card class="q-pa-md q-mt-md results-card">
            <div class="row items-start justify-between q-col-gutter-md">
                <div class="col-12 col-lg-8">
                    <div class="text-h6">Results Controls</div>
                    <div class="text-body2 text-grey-7 q-mt-xs">
                        Update the x-axis and split settings here, then apply them without
                        leaving the results view.
                    </div>
                </div>
            </div>

            <q-banner
                v-if="model.errorMsg"
                class="bg-negative text-white q-mt-md"
                rounded
            >
                {{ model.errorMsg }}
            </q-banner>

            <MortalityAeVariableControls :model="model" class="q-mt-md" />

            <div class="row items-center q-gutter-sm q-mt-md">
                <q-btn
                    label="Apply"
                    color="primary"
                    :disable="!model.canAnalyze || model.loading"
                    :loading="model.loading"
                    @click="handlers.onAnalyze"
                />
                <div v-if="model.loading" class="text-caption text-grey-7">
                    Updating results...
                </div>
            </div>

            <q-separator class="q-my-lg" />
            <div class="text-h6 q-mb-md">A/E Scatter</div>

            <q-expansion-item
                dense
                dense-toggle
                expand-separator
                label="Calculation Details"
                class="q-mb-md"
                header-class="text-caption text-grey-7"
            >
                <q-card flat bordered class="q-pa-md bg-grey-1">
                    <div class="text-body2">
                        <div class="text-weight-medium q-mb-sm">
                            A/E Calculation (within each bin/group):
                        </div>
                        <ul class="q-pl-md q-my-xs">
                            <li>
                                <strong>Count:</strong> Sum of MAC / Sum of MEC<br />
                                <span class="text-grey-7">
                                    (Total Actual Deaths / Total Expected Deaths)
                                </span>
                            </li>
                            <li class="q-mt-xs">
                                <strong>Amount:</strong> Sum of MAN / Sum of MEN<br />
                                <span class="text-grey-7">
                                    (Total Actual Claim Amount / Total Expected Claim Amount)
                                </span>
                            </li>
                        </ul>
                        <div class="text-weight-medium q-mb-sm q-mt-md">
                            95% Confidence Interval:
                        </div>
                        <ul class="q-pl-md q-my-xs">
                            <li>Calculated using Beta distribution with Jeffrey's prior</li>
                            <li class="q-mt-xs">
                                <strong>Count:</strong> Based on mortality rate within group
                            </li>
                            <li class="q-mt-xs">
                                <strong>Amount:</strong> Same rate CI scaled by average claim
                                amount per group
                                <ul class="q-pl-md" style="list-style-type: circle">
                                    <li>Uses actual average when deaths &gt; 0</li>
                                    <li>Uses expected average when deaths = 0</li>
                                </ul>
                            </li>
                        </ul>
                    </div>
                </q-card>
            </q-expansion-item>

            <div class="row q-col-gutter-md">
                <div class="col-12 col-md-6">
                    <div class="text-subtitle2 q-mb-sm text-center">A/E by Count</div>
                    <AeScatterPlot
                        :rows="model.aeResults.rows"
                        :x-axis-kind="model.resultsXAxisKind"
                        :variable-name="model.resultsVariableName || 'Variable'"
                        :numeric-domain="model.resultsXDomain"
                        :split-results="model.aeResults.split_results || null"
                        :split-variable-name="model.resultsSplitVariableName"
                        :poly-fit="model.aeResults.poly_fit || null"
                        metric="count"
                        v-model:show-overall="model.scatterShowOverall"
                        v-model:split-visible="model.scatterSplitVisible"
                    />
                </div>
                <div class="col-12 col-md-6">
                    <div class="text-subtitle2 q-mb-sm text-center">A/E by Amount</div>
                    <AeScatterPlot
                        :rows="model.aeResults.rows"
                        :x-axis-kind="model.resultsXAxisKind"
                        :variable-name="model.resultsVariableName || 'Variable'"
                        :numeric-domain="model.resultsXDomain"
                        :split-results="model.aeResults.split_results || null"
                        :split-variable-name="model.resultsSplitVariableName"
                        :poly-fit="model.aeResults.poly_fit || null"
                        metric="amount"
                        v-model:show-overall="model.scatterShowOverall"
                        v-model:split-visible="model.scatterSplitVisible"
                    />
                </div>
            </div>

            <div
                v-if="
                    model.aeResults.poly_fit ||
                    (model.aeResults.split_results &&
                        model.aeResults.split_results.some((split: any) => split.poly_fit))
                "
                class="q-mt-md q-pa-md bg-grey-1"
                style="border-radius: 4px"
            >
                <div class="text-subtitle2 text-weight-medium q-mb-sm">
                    Polynomial Best Fit
                </div>

                <div
                    v-if="model.aeResults.poly_fit && model.scatterShowOverall"
                    class="q-mb-sm"
                >
                    <div class="text-body2">
                        <span class="text-weight-medium">Overall:</span>
                        <span class="q-ml-sm equation">
                            {{ model.formatPolynomialEquation(model.aeResults.poly_fit) }}
                        </span>
                        <span
                            v-if="
                                model.aeResults.poly_fit.r2 !== null &&
                                model.aeResults.poly_fit.r2 !== undefined
                            "
                            class="q-ml-md text-grey-7"
                        >
                            (R^2 = {{ model.aeResults.poly_fit.r2.toFixed(3) }})
                        </span>
                    </div>
                </div>

                <div
                    v-if="
                        model.aeResults.split_results &&
                        model.aeResults.split_results.length
                    "
                    class="q-pl-md"
                >
                    <template
                        v-for="(split, idx) in model.aeResults.split_results"
                        :key="`poly-${idx}`"
                    >
                        <div
                            v-if="
                                split.poly_fit &&
                                model.scatterSplitVisible[split.split_group]
                            "
                            class="text-body2 q-mb-xs"
                        >
                            <span class="text-weight-medium">{{ split.split_group }}:</span>
                            <span class="q-ml-sm equation">
                                {{ model.formatPolynomialEquation(split.poly_fit) }}
                            </span>
                            <span
                                v-if="
                                    split.poly_fit.r2 !== null &&
                                    split.poly_fit.r2 !== undefined
                                "
                                class="q-ml-md text-grey-7"
                            >
                                (R^2 = {{ split.poly_fit.r2.toFixed(3) }})
                            </span>
                        </div>
                    </template>
                </div>
            </div>

            <q-separator class="q-my-md" />
            <div class="text-h6 q-mb-md">A/E Analysis</div>
            <q-tabs v-model="model.resultsTab" dense>
                <q-tab name="overall" label="Overall" />
                <q-tab
                    v-for="(split, idx) in model.aeResults.split_results || []"
                    :key="`split-tab-${idx}`"
                    :name="`split-${idx}`"
                    :label="model.splitTabLabel(split.split_group)"
                />
            </q-tabs>
            <q-separator />
            <q-tab-panels v-model="model.resultsTab" keep-alive>
                <q-tab-panel name="overall">
                    <AeUnivariateTable
                        :rows="model.aeResults.rows"
                        :variable-name="model.resultsVariableName || 'Variable'"
                        :x-axis-kind="model.resultsXAxisKind"
                    />
                    <q-separator class="q-my-md" />
                    <div class="text-subtitle1 q-mb-sm">A/E Treemaps</div>
                    <div class="row q-col-gutter-md">
                        <div class="col-12 col-md-6">
                            <div class="text-subtitle2 q-mb-sm text-center">
                                A/E by Count (Area = Policy Count)
                            </div>
                            <AeTreemap
                                :rows="model.aeResults.rows"
                                :variable-name="model.resultsVariableName || 'Variable'"
                                :split-results="model.aeResults.split_results || null"
                                :split-variable-name="model.resultsSplitVariableName"
                                :split-x-axis-kind="model.resultsSplitXAxisKind"
                                metric="count"
                                v-model:show-overall="model.currentTreemapShowOverall"
                                v-model:split-visible="model.currentTreemapSplitVisible"
                            />
                        </div>
                        <div class="col-12 col-md-6">
                            <div class="text-subtitle2 q-mb-sm text-center">
                                A/E by Amount (Area = Face Amount)
                            </div>
                            <AeTreemap
                                :rows="model.aeResults.rows"
                                :variable-name="model.resultsVariableName || 'Variable'"
                                :split-results="model.aeResults.split_results || null"
                                :split-variable-name="model.resultsSplitVariableName"
                                :split-x-axis-kind="model.resultsSplitXAxisKind"
                                metric="amount"
                                v-model:show-overall="model.currentTreemapShowOverall"
                                v-model:split-visible="model.currentTreemapSplitVisible"
                            />
                        </div>
                    </div>
                </q-tab-panel>
                <q-tab-panel
                    v-for="(split, idx) in model.aeResults.split_results || []"
                    :key="`split-panel-${idx}`"
                    :name="`split-${idx}`"
                >
                    <AeUnivariateTable
                        :rows="split.rows"
                        :variable-name="model.resultsVariableName || 'Variable'"
                        :x-axis-kind="model.resultsXAxisKind"
                    />
                    <q-separator class="q-my-md" />
                    <div class="text-subtitle1 q-mb-sm">A/E Treemaps</div>
                    <div class="row q-col-gutter-md">
                        <div class="col-12 col-md-6">
                            <div class="text-subtitle2 q-mb-sm text-center">
                                A/E by Count (Area = Policy Count)
                            </div>
                            <AeTreemap
                                :rows="split.rows"
                                :variable-name="model.resultsVariableName || 'Variable'"
                                :split-results="model.aeResults.split_results || null"
                                :split-variable-name="model.resultsSplitVariableName"
                                :split-x-axis-kind="model.resultsSplitXAxisKind"
                                metric="count"
                                v-model:show-overall="model.currentTreemapShowOverall"
                                v-model:split-visible="model.currentTreemapSplitVisible"
                            />
                        </div>
                        <div class="col-12 col-md-6">
                            <div class="text-subtitle2 q-mb-sm text-center">
                                A/E by Amount (Area = Face Amount)
                            </div>
                            <AeTreemap
                                :rows="split.rows"
                                :variable-name="model.resultsVariableName || 'Variable'"
                                :split-results="model.aeResults.split_results || null"
                                :split-variable-name="model.resultsSplitVariableName"
                                :split-x-axis-kind="model.resultsSplitXAxisKind"
                                metric="amount"
                                v-model:show-overall="model.currentTreemapShowOverall"
                                v-model:split-visible="model.currentTreemapSplitVisible"
                            />
                        </div>
                    </div>
                </q-tab-panel>
            </q-tab-panels>

            <div
                v-if="
                    model.aeResults.cola_m1_stacked?.causes?.length ||
                    model.aeResults.split_results?.some(
                        (split: any) => split.cola_m1_stacked?.causes?.length,
                    )
                "
            >
                <q-separator class="q-my-lg" />
                <div class="text-h6 q-mb-md">Claim Analysis by Cause of Death</div>
                <q-tabs v-model="model.colaResultsTab" dense>
                    <q-tab name="overall" label="Overall" />
                    <q-tab
                        v-for="(split, idx) in model.aeResults.split_results || []"
                        :key="`cola-split-tab-${idx}`"
                        :name="`split-${idx}`"
                        :label="model.splitTabLabel(split.split_group)"
                    />
                </q-tabs>
                <q-separator />
                <q-tab-panels v-model="model.colaResultsTab" keep-alive>
                    <q-tab-panel name="overall">
                        <div v-if="model.aeResults.cola_m1_stacked?.causes?.length">
                            <AeColaClaimTable
                                :data="model.aeResults.cola_m1_stacked"
                                :variable-name="model.resultsVariableName || 'Variable'"
                            />
                            <div class="q-mt-lg cola-visual">
                                <div class="text-subtitle2 q-mb-sm text-center">
                                    Visual Distribution
                                </div>
                                <AeColaM1StackedBars
                                    style="width: 100%"
                                    :data="model.aeResults.cola_m1_stacked"
                                />
                            </div>
                        </div>
                    </q-tab-panel>
                    <q-tab-panel
                        v-for="(split, idx) in model.aeResults.split_results || []"
                        :key="`cola-split-panel-${idx}`"
                        :name="`split-${idx}`"
                    >
                        <div v-if="split.cola_m1_stacked?.causes?.length">
                            <AeColaClaimTable
                                :data="split.cola_m1_stacked"
                                :variable-name="model.resultsVariableName || 'Variable'"
                            />
                            <div class="q-mt-lg cola-visual">
                                <div class="text-subtitle2 q-mb-sm text-center">
                                    Visual Distribution
                                </div>
                                <AeColaM1StackedBars
                                    style="width: 100%"
                                    :data="split.cola_m1_stacked"
                                />
                            </div>
                        </div>
                    </q-tab-panel>
                </q-tab-panels>
            </div>

            <q-inner-loading :showing="model.loading">
                <div class="column items-center q-gutter-sm">
                    <q-spinner color="primary" size="42px" />
                    <div class="text-caption text-grey-7">Updating results...</div>
                </div>
            </q-inner-loading>
        </q-card>
    </div>
</template>

<script setup lang="ts">
import AeColaClaimTable from './AeColaClaimTable.vue';
import AeColaM1StackedBars from './AeColaM1StackedBars.vue';
import AeScatterPlot from './AeScatterPlot.vue';
import AeTreemap from './AeTreemap.vue';
import AeUnivariateTable from './AeUnivariateTable.vue';
import MortalityAeVariableControls from './MortalityAeVariableControls.vue';

defineProps<{
    model: Record<string, any>;
    handlers: Record<string, any>;
}>();
</script>

<style scoped>
.results-card {
    position: relative;
}

.cola-visual {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.equation {
    font-family: 'Courier New', monospace;
}
</style>
