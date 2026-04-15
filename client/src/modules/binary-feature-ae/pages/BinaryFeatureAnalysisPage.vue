<template>
    <q-page class="q-pa-md">
        <div class="page-shell">
            <q-banner class="q-px-md q-pt-md q-pb-sm">
                <div class="row items-center q-gutter-x-sm">
                    <span class="text-h4">Binary Feature Mortality A/E</span>
                </div>
                <div class="text-body2 text-grey-7 q-mt-xs">
                    Filter the saved ruleset, inspect a focused rule, compare selected
                    rules, and pin triage candidates for follow-up.
                </div>
            </q-banner>

            <q-banner
                v-if="missingConfigMessage"
                class="bg-warning text-black q-mt-md"
                rounded
            >
                {{ missingConfigMessage }}
            </q-banner>

            <q-banner
                v-if="errorMsg"
                class="bg-negative text-white q-mt-md"
                rounded
            >
                {{ errorMsg }}
            </q-banner>

            <q-card flat bordered class="q-mt-md">
                <q-card-section>
                    <div class="text-h6">Filters</div>
                    <div class="text-body2 text-grey-7">
                        {{ responseData?.dataset_name || activeDatasetName || 'Saved ruleset' }}
                    </div>
                </q-card-section>

                <q-card-section class="q-pt-none">
                    <div class="row q-col-gutter-md">
                        <div class="col-12 col-md-4">
                            <q-select
                                v-model="categories"
                                :options="categoryOptions"
                                label="Category"
                                emit-value
                                map-options
                                multiple
                                outlined
                                dense
                                options-dense
                                clearable
                            />
                        </div>
                        <div class="col-12 col-md-4">
                            <q-select
                                v-model="significanceValues"
                                :options="significanceOptions"
                                label="Significance"
                                emit-value
                                map-options
                                multiple
                                outlined
                                dense
                                options-dense
                            />
                        </div>
                        <div class="col-12 col-md-4">
                            <q-input
                                v-model="searchText"
                                outlined
                                dense
                                label="Search"
                                placeholder="Rule id, name, category"
                                clearable
                            />
                        </div>
                    </div>

                    <div class="row q-col-gutter-md q-mt-sm">
                        <div class="col-12 col-md-3">
                            <q-input
                                v-model.number="minHitCount"
                                type="number"
                                outlined
                                dense
                                label="Min Hit Count"
                            />
                        </div>
                        <div class="col-12 col-md-3">
                            <q-input
                                v-model.number="minClaimCount"
                                type="number"
                                outlined
                                dense
                                label="Min Claim Count"
                            />
                        </div>
                        <div class="col-12 col-md-3">
                            <div class="text-caption text-grey-7 q-mb-xs">Bubble Size</div>
                            <q-btn-toggle
                                v-model="sizeBy"
                                spread
                                unelevated
                                toggle-color="primary"
                                :options="[
                                    { label: 'Hit Count', value: 'hit_count' },
                                    { label: 'Claim Count', value: 'claim_count' },
                                ]"
                            />
                        </div>
                        <div class="col-12 col-md-3">
                            <div class="text-caption text-grey-7 q-mb-xs">
                                Confidence Interval Level
                            </div>
                            <q-btn-toggle
                                v-model="ciLevel"
                                spread
                                unelevated
                                toggle-color="primary"
                                :options="ciLevelToggleOptions"
                            />
                        </div>
                    </div>

                    <div class="q-mt-md">
                        <div class="row items-center justify-between q-mb-xs">
                            <div class="text-caption text-grey-7">Y-Axis Display Cap</div>
                            <div class="text-caption text-grey-7">
                                {{ displayCap.toFixed(1) }}
                            </div>
                        </div>
                        <q-slider
                            v-model="displayCap"
                            :min="0"
                            :max="5"
                            :step="0.1"
                            label
                            switch-label-side
                        />
                    </div>
                </q-card-section>
            </q-card>

            <div
                v-if="responseData"
                class="kpi-grid q-mt-md"
            >
                <q-card flat bordered class="kpi-card">
                    <q-card-section>
                        <div class="text-caption text-grey-7">Visible Rules</div>
                        <div class="text-h5">{{ formatWholeNumber(responseData.kpis.visible_rule_count) }}</div>
                    </q-card-section>
                </q-card>
                <q-card flat bordered class="kpi-card">
                    <q-card-section>
                        <div class="text-caption text-grey-7">Median Hit Rate</div>
                        <div class="text-h5">{{ formatPercentFromRatio(responseData.kpis.median_hit_rate) }}</div>
                    </q-card-section>
                </q-card>
                <q-card flat bordered class="kpi-card">
                    <q-card-section>
                        <div class="text-caption text-grey-7">Median Claim Count</div>
                        <div class="text-h5">{{ formatWholeNumber(responseData.kpis.median_claim_count) }}</div>
                    </q-card-section>
                </q-card>
                <q-card flat bordered class="kpi-card">
                    <q-card-section>
                        <div class="text-caption text-grey-7">Median A/E</div>
                        <div class="text-h5">{{ responseData.kpis.median_ae.toFixed(3) }}</div>
                    </q-card-section>
                </q-card>
                <q-card flat bordered class="kpi-card">
                    <q-card-section>
                        <div class="text-caption text-grey-7">Elevated</div>
                        <div class="text-h5">{{ formatWholeNumber(responseData.kpis.elevated_count) }}</div>
                    </q-card-section>
                </q-card>
                <q-card flat bordered class="kpi-card">
                    <q-card-section>
                        <div class="text-caption text-grey-7">Uncertain</div>
                        <div class="text-h5">{{ formatWholeNumber(responseData.kpis.uncertain_count) }}</div>
                    </q-card-section>
                </q-card>
                <q-card flat bordered class="kpi-card">
                    <q-card-section>
                        <div class="text-caption text-grey-7">Below Expected</div>
                        <div class="text-h5">
                            {{ formatWholeNumber(responseData.kpis.below_expected_count) }}
                        </div>
                    </q-card-section>
                </q-card>
            </div>

            <div class="row q-col-gutter-md q-mt-md">
                <div class="col-12 col-lg-8">
                    <q-card flat bordered>
                        <q-card-section>
                            <div class="text-h6">Rule Scatter</div>
                        </q-card-section>
                        <q-card-section class="q-pt-none scatter-card">
                            <BinaryFeatureScatterPlot
                                :rows="rows"
                                :size-by="sizeBy"
                                :display-cap="displayCap"
                                :selected-row-ids="selectedRowIds"
                                :focused-row-id="focusedRowId"
                                @update:selected-row-ids="selectedRowIds = $event"
                                @focus-row="focusedRowId = $event"
                            />
                            <q-inner-loading :showing="loading">
                                <q-spinner color="primary" size="42px" />
                            </q-inner-loading>
                        </q-card-section>
                    </q-card>

                </div>
                <div class="col-12 col-lg-4">
                    <BinaryFeatureDetailCards
                        :rows="rows"
                        :focused-row-id="focusedRowId"
                        :ci-level="ciLevel"
                        :show-charts="false"
                    />

                    <q-card flat bordered class="q-mt-md">
                        <q-card-section class="row items-center justify-between">
                            <div class="text-h6">Pinned Rules</div>
                            <div class="row q-gutter-sm">
                                <q-btn
                                    label="Pin Focused Rule"
                                    color="primary"
                                    unelevated
                                    dense
                                    :disable="!focusedRow"
                                    @click="pinFocusedRule"
                                />
                                <q-btn
                                    label="Clear Pins"
                                    color="grey-7"
                                    flat
                                    dense
                                    :disable="pinnedRules.length === 0"
                                    @click="clearPins"
                                />
                            </div>
                        </q-card-section>
                        <q-card-section>
                            <div
                                v-if="!pinnedRules.length"
                                class="text-grey-7"
                            >
                                No pinned rules yet.
                            </div>
                            <q-list v-else dense separator>
                                <q-item
                                    v-for="rule in pinnedRules"
                                    :key="rule.row_id"
                                >
                                    <q-item-section>
                                        <q-item-label class="text-weight-medium">
                                            {{ rule.rule }}
                                        </q-item-label>
                                        <q-item-label caption>
                                            {{ rule.RuleName }}
                                        </q-item-label>
                                    </q-item-section>
                                    <q-item-section side top>
                                        <div class="text-caption">A/E {{ rule.ae_ratio.toFixed(3) }}</div>
                                        <q-badge color="grey-8" class="q-mt-xs">
                                            {{ rule.significance_class }}
                                        </q-badge>
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </q-card-section>
                    </q-card>
                </div>
            </div>

            <div class="q-mt-md">
                <BinaryFeatureDetailCards
                    :rows="rows"
                    :focused-row-id="focusedRowId"
                    :ci-level="ciLevel"
                    :show-summary="false"
                />
            </div>

            <q-card flat bordered class="q-mt-md">
                <q-card-section>
                    <div class="text-h6">Compare / Triage Table</div>
                </q-card-section>
                <q-card-section class="q-pt-none">
                    <BinaryFeatureGrid
                        :rows="rows"
                        :selected-row-ids="selectedRowIds"
                        @update:selected-row-ids="selectedRowIds = $event"
                        @focus-row="focusedRowId = $event"
                    />
                </q-card-section>
            </q-card>

            <div class="q-mt-md">
                <BinaryFeatureCompareCharts :selected-rows="selectedRows" />
            </div>
        </div>
    </q-page>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import BinaryFeatureCompareCharts from '@/modules/binary-feature-ae/components/BinaryFeatureCompareCharts.vue';
import BinaryFeatureDetailCards from '@/modules/binary-feature-ae/components/BinaryFeatureDetailCards.vue';
import BinaryFeatureGrid from '@/modules/binary-feature-ae/components/BinaryFeatureGrid.vue';
import BinaryFeatureScatterPlot from '@/modules/binary-feature-ae/components/BinaryFeatureScatterPlot.vue';
import {
    BINARY_FEATURE_PERFORMANCE_TYPE,
    CI_LEVEL_OPTIONS,
    SIGNIFICANCE_OPTIONS,
} from '@/modules/binary-feature-ae/constants';
import {
    isBinaryFeatureDatasetConfig,
    type ApiDatasetConfig,
} from '@/types/dataset-config';
import type {
    ApiBinaryFeatureCalculateResponse,
    ApiBinaryFeatureRow,
    BinaryFeatureCiLevel,
    BinaryFeaturePinnedRule,
    BinaryFeatureSignificance,
} from '@/types/binary-feature-ae';
import {
    formatPercentFromRatio,
    formatWholeNumber,
} from '@/utils/format';
import {
    getDatasetConfig,
    postBinaryFeatureCalculate,
} from '@/utils/api';

const route = useRoute();

const loading = ref(false);
const errorMsg = ref<string | null>(null);
const responseData = ref<ApiBinaryFeatureCalculateResponse | null>(null);
const activeDatasetName = ref<string | null>(null);

const categories = ref<string[]>([]);
const significanceValues = ref<BinaryFeatureSignificance[]>([...SIGNIFICANCE_OPTIONS]);
const searchText = ref('');
const minHitCount = ref<number | null>(0);
const minClaimCount = ref<number | null>(5);
const ciLevel = ref<BinaryFeatureCiLevel>('95');
const sizeBy = ref<'hit_count' | 'claim_count'>('hit_count');
const displayCap = ref(2.0);

const selectedRowIds = ref<string[]>([]);
const focusedRowId = ref<string | null>(null);
const pinnedRules = ref<BinaryFeaturePinnedRule[]>([]);

const activeConfig = ref<ApiDatasetConfig | null>(null);
let abortController: AbortController | null = null;

const configId = computed(() => {
    const raw = route.query.config;
    return typeof raw === 'string' && raw.trim() ? raw : null;
});

const missingConfigMessage = computed(() => {
    if (configId.value) {
        return null;
    }
    return 'Open this module from Central Setup or a saved configuration so the analysis can load a config-backed dataset.';
});

const categoryOptions = computed(() => {
    return (responseData.value?.available_categories ?? []).map((category) => ({
        label: category,
        value: category,
    }));
});

const significanceOptions = SIGNIFICANCE_OPTIONS.map((value) => ({
    label: value,
    value,
}));

const ciLevelToggleOptions = CI_LEVEL_OPTIONS.map((value) => ({
    label: `${value}%`,
    value,
}));

const rows = computed(() => responseData.value?.rows ?? []);

const focusedRow = computed(() => {
    if (!focusedRowId.value) {
        return null;
    }
    return rows.value.find((row) => row.row_id === focusedRowId.value) ?? null;
});

const selectedRows = computed(() => {
    return rows.value.filter((row) => selectedRowIds.value.includes(row.row_id));
});

function useDebouncedRef<T>(source: { value: T }, delayMs: number) {
    const debounced = ref(source.value) as { value: T };
    let timer: number | null = null;

    watch(
        () => source.value,
        (value) => {
            if (timer !== null) {
                window.clearTimeout(timer);
            }
            timer = window.setTimeout(() => {
                debounced.value = value;
            }, delayMs);
        },
    );

    onBeforeUnmount(() => {
        if (timer !== null) {
            window.clearTimeout(timer);
        }
    });

    return debounced;
}

const debouncedSearchText = useDebouncedRef(searchText, 250);
const debouncedMinHitCount = useDebouncedRef(minHitCount, 250);
const debouncedMinClaimCount = useDebouncedRef(minClaimCount, 250);

function resetInteractionState() {
    activeConfig.value = null;
    activeDatasetName.value = null;
    responseData.value = null;
    errorMsg.value = null;
    categories.value = [];
    significanceValues.value = [...SIGNIFICANCE_OPTIONS];
    searchText.value = '';
    minHitCount.value = 0;
    minClaimCount.value = 5;
    ciLevel.value = '95';
    sizeBy.value = 'hit_count';
    displayCap.value = 2.0;
    selectedRowIds.value = [];
    focusedRowId.value = null;
    pinnedRules.value = [];
}

async function ensureBinaryFeatureConfig() {
    if (!configId.value) {
        activeConfig.value = null;
        activeDatasetName.value = null;
        return false;
    }

    const config = await getDatasetConfig(configId.value);
    if (!isBinaryFeatureDatasetConfig(config)) {
        throw new Error('Selected configuration is not a Binary Feature Mortality A/E config.');
    }
    if (config.performance_type !== BINARY_FEATURE_PERFORMANCE_TYPE) {
        throw new Error('Selected configuration uses an unexpected performance type.');
    }

    activeConfig.value = config;
    activeDatasetName.value = config.dataset_name;
    return true;
}

async function loadData() {
    if (!configId.value || !activeConfig.value) {
        return;
    }

    abortController?.abort();
    abortController = new AbortController();
    const signal = abortController.signal;

    loading.value = true;
    errorMsg.value = null;

    try {
        const result = await postBinaryFeatureCalculate(
            {
                config_id: configId.value,
                ci_level: ciLevel.value,
                categories: categories.value,
                significance_values: significanceValues.value,
                search_text: debouncedSearchText.value || null,
                min_hit_count: debouncedMinHitCount.value,
                min_claim_count: debouncedMinClaimCount.value,
            },
            signal,
        );

        responseData.value = result;
    } catch (err) {
        if (signal.aborted) {
            return;
        }
        errorMsg.value = err instanceof Error ? err.message : String(err);
    } finally {
        if (!signal.aborted) {
            loading.value = false;
        }
    }
}

function pinFocusedRule() {
    if (!focusedRow.value) {
        return;
    }

    if (pinnedRules.value.some((row) => row.row_id === focusedRow.value?.row_id)) {
        return;
    }

    pinnedRules.value = [
        ...pinnedRules.value,
        {
            row_id: focusedRow.value.row_id,
            rule: focusedRow.value.rule,
            RuleName: focusedRow.value.RuleName,
            ae_ratio: focusedRow.value.ae_ratio,
            significance_class: focusedRow.value.significance_class,
        },
    ];
}

function clearPins() {
    pinnedRules.value = [];
}

watch(
    () => configId.value,
    async () => {
        resetInteractionState();

        if (!configId.value) {
            return;
        }

        try {
            await ensureBinaryFeatureConfig();
        } catch (err) {
            errorMsg.value = err instanceof Error ? err.message : String(err);
        }
    },
    { immediate: true },
);

watch(
    () => [
        configId.value,
        activeConfig.value?.id,
        categories.value,
        significanceValues.value,
        ciLevel.value,
        debouncedSearchText.value,
        debouncedMinHitCount.value,
        debouncedMinClaimCount.value,
    ],
    () => {
        if (!configId.value || !activeConfig.value) {
            return;
        }
        void loadData();
    },
    { deep: true },
);

watch(
    () => rows.value,
    (nextRows) => {
        const rowIds = new Set(nextRows.map((row) => row.row_id));
        selectedRowIds.value = selectedRowIds.value.filter((rowId) => rowIds.has(rowId));
        if (focusedRowId.value && !rowIds.has(focusedRowId.value)) {
            focusedRowId.value = selectedRowIds.value[0] ?? null;
        }
    },
    { deep: true },
);

watch(
    () => selectedRowIds.value,
    (ids) => {
        if (!ids.length) {
            return;
        }
        if (!focusedRowId.value || !ids.includes(focusedRowId.value)) {
            focusedRowId.value = ids[0];
        }
    },
    { deep: true },
);

watch(
    () => responseData.value?.available_categories,
    (availableCategories) => {
        if (!availableCategories) {
            return;
        }

        const nextCategories = categories.value.filter((category) =>
            availableCategories.includes(category),
        );

        if (nextCategories.length !== categories.value.length) {
            categories.value = nextCategories;
        }
    },
);

onMounted(() => {
    if (!configId.value) {
        errorMsg.value = null;
    }
});

onBeforeUnmount(() => {
    abortController?.abort();
});
</script>

<style scoped>
.page-shell {
    max-width: 100%;
}

.kpi-grid {
    display: grid;
    gap: 12px;
    grid-template-columns: repeat(7, minmax(150px, 1fr));
}

.kpi-card {
    min-height: 108px;
}

.scatter-card {
    position: relative;
}

@media (max-width: 1200px) {
    .kpi-grid {
        grid-template-columns: repeat(3, minmax(150px, 1fr));
    }
}

@media (max-width: 720px) {
    .kpi-grid {
        grid-template-columns: repeat(1, minmax(150px, 1fr));
    }
}
</style>
