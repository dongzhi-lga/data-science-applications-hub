<template>
    <q-page class="q-pa-md bg-grey-1">
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
                v-if="errorMsg"
                class="bg-negative text-white q-mt-md"
                rounded
            >
                {{ errorMsg }}
            </q-banner>

            <q-card class="q-mt-md filter-card">
                <q-card-section>
                    <div class="text-h6">Inputs</div>
                    <div class="text-body2 text-grey-7">
                        Choose a saved Binary Feature dataset configuration from Central
                        Setup.
                    </div>
                </q-card-section>

                <q-card-section class="q-pt-none">
                    <div class="row items-center q-col-gutter-md q-mb-md">
                        <div class="col-12">
                            <q-select
                                v-model="selectedConfigId"
                                :options="configOptions"
                                emit-value
                                map-options
                                outlined
                                dense
                                label="Select Saved Dataset Configuration"
                                class="input-600"
                                clearable
                                :loading="configsLoading"
                                hint="Choose a previously configured dataset from Central Setup"
                            >
                                <template #prepend>
                                    <q-icon name="folder_open" />
                                </template>
                            </q-select>
                        </div>
                    </div>

                    <div v-if="activeConfig">
                        <q-banner class="bg-green-1" dense>
                            <template #avatar>
                                <q-icon name="check_circle" color="positive" />
                            </template>
                            <strong>{{
                                selectedConfig?.dataset_name || activeConfig.dataset_name
                            }}</strong>
                            loaded successfully
                            <br />File and column mappings loaded automatically from the
                            saved configuration
                        </q-banner>
                    </div>

                    <div v-else-if="!configsLoading && !hasSavedConfigs">
                        <q-banner class="bg-grey-3" dense>
                            <template #avatar>
                                <q-icon name="info" color="grey-7" />
                            </template>
                            No saved Binary Feature configurations were found. Go to
                            <strong>Central Setup</strong> to upload a file and save a
                            configuration first.
                        </q-banner>
                    </div>

                    <div v-else>
                        <q-banner class="bg-grey-3" dense>
                            <template #avatar>
                                <q-icon name="info" color="grey-7" />
                            </template>
                            Select a saved Binary Feature dataset configuration above to
                            load a ruleset for analysis.
                        </q-banner>
                    </div>
                </q-card-section>
            </q-card>

            <template v-if="activeConfig">
                <q-card class="q-mt-md filter-card">
                    <q-card-section>
                        <div class="text-h6">Filters</div>
                        <div class="text-body2 text-grey-7">
                            {{
                                responseData?.dataset_name ||
                                selectedConfig?.dataset_name ||
                                activeDatasetName ||
                                'Saved ruleset'
                            }}
                        </div>
                    </q-card-section>

                    <q-card-section class="q-pt-none">
                        <div class="row">
                            <div class="col-12 col-md-6">
                                <!-- Row 1: Category + Search -->
                                <div class="row q-col-gutter-md">
                                    <div class="col-12 col-sm-6">
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
                                    <div class="col-12 col-sm-6">
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

                                <!-- Row 2: Min Hit Count + Min Claim Count -->
                                <div class="row q-col-gutter-md q-mt-sm">
                                    <div class="col-12 col-sm-6">
                                        <q-input
                                            v-model.number="minHitCount"
                                            type="number"
                                            outlined
                                            dense
                                            label="Min Hit Count"
                                        />
                                    </div>
                                    <div class="col-12 col-sm-6">
                                        <q-input
                                            v-model.number="minClaimCount"
                                            type="number"
                                            outlined
                                            dense
                                            label="Min Claim Count"
                                        />
                                    </div>
                                </div>

                                <!-- Row 3: Perspective + Confidence Interval Level + Significance -->
                                <div class="filter-group q-mt-sm">
                                    <div class="row q-col-gutter-md">
                                        <div class="col-12 col-sm-4">
                                            <div class="text-caption text-grey-7 q-mb-xs filter-group-label">
                                                Perspective
                                            </div>
                                            <q-option-group
                                                v-model="perspective"
                                                :options="perspectiveOptions"
                                                type="radio"
                                                inline
                                                dense
                                                color="primary"
                                                class="filter-option-group"
                                            />
                                        </div>
                                        <div class="col-12 col-sm-4">
                                            <div class="text-caption text-grey-7 q-mb-xs filter-group-label">
                                                Confidence Interval Level
                                            </div>
                                            <q-option-group
                                                v-model="ciLevel"
                                                :options="ciLevelRadioOptions"
                                                type="radio"
                                                inline
                                                dense
                                                color="primary"
                                                class="filter-option-group"
                                            />
                                        </div>
                                        <div class="col-12 col-sm-4">
                                            <div class="text-caption text-grey-7 q-mb-xs filter-group-label">
                                                Significance
                                            </div>
                                            <q-option-group
                                                v-model="significanceValues"
                                                :options="significanceOptions"
                                                type="checkbox"
                                                inline
                                                dense
                                                color="primary"
                                                class="filter-option-group"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <!-- Axis Controls -->
                                <div class="filter-group q-mt-sm">
                                    <!-- Row 4: X-Axis Display Cap -->
                                    <div>
                                        <div class="text-caption text-grey-7 q-mb-xs">
                                            X-Axis Display Cap
                                        </div>
                                        <div class="row items-center q-gutter-x-sm no-wrap">
                                            <q-slider
                                                v-model="xDisplayCap"
                                                :min="0"
                                                :max="100"
                                                :step="1"
                                                class="col"
                                            />
                                            <q-input
                                                v-model.number="xDisplayCap"
                                                type="number"
                                                dense
                                                outlined
                                                suffix="%"
                                                style="width: 88px"
                                                @blur="clampX"
                                            />
                                        </div>
                                    </div>

                                    <!-- Row 5: Y-Axis Display Cap -->
                                    <div class="q-mt-md">
                                        <div class="text-caption text-grey-7 q-mb-xs">
                                            Y-Axis Display Cap
                                        </div>
                                        <div class="row items-center q-gutter-x-sm no-wrap">
                                            <q-slider
                                                v-model="yDisplayCap"
                                                :min="0"
                                                :max="5"
                                                :step="0.1"
                                                class="col"
                                            />
                                            <q-input
                                                v-model.number="yDisplayCap"
                                                type="number"
                                                dense
                                                outlined
                                                inputmode="decimal"
                                                style="width: 80px"
                                                @blur="clampY"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>

                <q-card
                    v-if="loading && !responseData"
                    class="q-mt-md section-card"
                >
                    <q-card-section class="row items-center q-gutter-sm">
                        <q-spinner color="primary" size="24px" />
                        <span class="text-body2">Loading saved ruleset...</span>
                    </q-card-section>
                </q-card>

                <div
                    v-if="responseData"
                    class="q-mt-md"
                >
                    <div class="row items-center justify-between q-mb-sm">
                        <div class="text-h6">{{ perspectiveLabel }} Perspective KPIs</div>
                        <q-badge color="primary" outline>
                            {{ perspectiveLabel }} Perspective
                        </q-badge>
                    </div>
                    <div class="kpi-grid">
                        <q-card class="kpi-card">
                            <q-card-section>
                                <div class="text-caption text-grey-7">Visible Rules</div>
                                <div class="text-h5">
                                    {{ formatWholeNumber(responseData.kpis.visible_rule_count) }}
                                </div>
                            </q-card-section>
                        </q-card>
                        <q-card class="kpi-card">
                            <q-card-section>
                                <div class="text-caption text-grey-7">Median Hit Rate</div>
                                <div class="text-h5">
                                    {{ formatPercentFromRatio(responseData.kpis.median_hit_rate) }}
                                </div>
                            </q-card-section>
                        </q-card>
                        <q-card class="kpi-card">
                            <q-card-section>
                                <div class="text-caption text-grey-7">
                                    {{ activeClaimMetricLabel }}
                                </div>
                                <div class="text-h5">
                                    {{
                                        displayedPerspective === 'count'
                                            ? formatWholeNumber(responseData.kpis.median_claim_count)
                                            : formatCurrency(responseData.kpis.median_claim_amount)
                                    }}
                                </div>
                            </q-card-section>
                        </q-card>
                        <q-card class="kpi-card">
                            <q-card-section>
                                <div class="text-caption text-grey-7">
                                    Median A/E ({{ perspectiveLabel }})
                                </div>
                                <div class="text-h5">
                                    {{ responseData.kpis.median_ae.toFixed(3) }}
                                </div>
                            </q-card-section>
                        </q-card>
                        <q-card class="kpi-card">
                            <q-card-section>
                                <div class="text-caption text-grey-7">Elevated</div>
                                <div class="text-h5">
                                    {{ formatWholeNumber(responseData.kpis.elevated_count) }}
                                </div>
                            </q-card-section>
                        </q-card>
                        <q-card class="kpi-card">
                            <q-card-section>
                                <div class="text-caption text-grey-7">Uncertain</div>
                                <div class="text-h5">
                                    {{ formatWholeNumber(responseData.kpis.uncertain_count) }}
                                </div>
                            </q-card-section>
                        </q-card>
                        <q-card class="kpi-card">
                            <q-card-section>
                                <div class="text-caption text-grey-7">Below Expected</div>
                                <div class="text-h5">
                                    {{ formatWholeNumber(responseData.kpis.below_expected_count) }}
                                </div>
                            </q-card-section>
                        </q-card>
                    </div>
                </div>

                <div
                    v-if="responseData"
                    class="row q-col-gutter-md q-mt-md"
                >
                    <div class="col-12 col-lg-8">
                        <q-card class="section-card">
                            <q-card-section>
                                <div class="row items-start q-col-gutter-md">
                                    <div class="col-12 col-md">
                                        <div class="text-h6">Rule Scatter</div>
                                        <div class="text-caption text-grey-7">
                                            {{ perspectiveLabel }} perspective
                                        </div>
                                    </div>
                                    <div class="col-12 col-md-auto">
                                        <div class="text-caption text-grey-7 q-mb-xs">
                                            Bubble Size
                                        </div>
                                        <q-option-group
                                            v-model="sizeBy"
                                            type="radio"
                                            inline
                                            dense
                                            color="primary"
                                            :options="sizeByOptions"
                                            class="filter-option-group"
                                        />
                                    </div>
                                </div>
                            </q-card-section>
                            <q-card-section class="q-pt-none scatter-card">
                                <BinaryFeatureScatterPlot
                                    :rows="rows"
                                    :perspective="displayedPerspective"
                                    :size-by="sizeBy"
                                    :display-cap="yDisplayCap"
                                    :x-display-cap="xDisplayCap"
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
                            :perspective="displayedPerspective"
                            :focused-row-id="focusedRowId"
                            :ci-level="ciLevel"
                            :show-charts="false"
                        />

                        <BinaryFeatureAiPanel
                            class="q-mt-md"
                            :focused-row="focusedRow"
                            :is-stale="isAiExplainStale"
                            :result="aiExplainResponse"
                            :loading="aiExplainLoading"
                            :error="aiExplainError"
                            @explain="onExplainRule"
                            @focus-row="focusEvidenceRow"
                        />

                        <q-card class="q-mt-md section-card">
                            <q-card-section class="row items-center justify-between">
                                <div>
                                    <div class="text-h6">Pinned Rules</div>
                                    <div class="text-caption text-grey-7">
                                        {{ perspectiveLabel }} perspective values
                                    </div>
                                </div>
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
                                        :disable="pinnedRuleKeys.length === 0"
                                        @click="clearPins"
                                    />
                                </div>
                            </q-card-section>
                            <q-card-section>
                                <div
                                    v-if="!pinnedRuleKeys.length"
                                    class="text-grey-7"
                                >
                                    No pinned rules yet.
                                </div>
                                <div
                                    v-else-if="!pinnedRules.length && hasHiddenPins"
                                    class="text-grey-7"
                                >
                                    Pinned rules are outside the current result set.
                                </div>
                                <q-list v-else dense separator>
                                    <q-item
                                        v-for="rule in pinnedRules"
                                        :key="rule.rule_key"
                                    >
                                        <q-item-section>
                                            <q-item-label class="text-weight-medium">
                                                {{ rule.rule }}
                                            </q-item-label>
                                            <q-item-label caption>
                                                {{ rule.RuleName }} | {{ rule.first_date }}
                                            </q-item-label>
                                        </q-item-section>
                                        <q-item-section side top>
                                            <div class="text-caption">
                                                {{ perspectiveLabel }} A/E
                                                {{ rule.ae_ratio.toFixed(3) }}
                                            </div>
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

                <div
                    v-if="responseData"
                    class="q-mt-md"
                >
                    <BinaryFeatureDetailCards
                        :rows="rows"
                        :perspective="displayedPerspective"
                        :focused-row-id="focusedRowId"
                        :ci-level="ciLevel"
                        :show-summary="false"
                    />
                </div>

                <q-card
                    v-if="responseData"
                    class="q-mt-md section-card"
                >
                    <q-card-section>
                        <div class="text-h6">
                            Compare / Triage Table ({{ perspectiveLabel }} Perspective)
                        </div>
                    </q-card-section>
                    <q-card-section class="q-pt-none">
                        <BinaryFeatureGrid
                            :rows="rows"
                            :perspective="displayedPerspective"
                            :ci-level="ciLevel"
                            :selected-row-ids="selectedRowIds"
                            @update:selected-row-ids="selectedRowIds = $event"
                            @focus-row="focusedRowId = $event"
                        />
                    </q-card-section>
                </q-card>

                <div
                    v-if="responseData"
                    class="q-mt-md"
                >
                    <BinaryFeatureCompareCharts
                        :selected-rows="selectedRows"
                        :perspective="displayedPerspective"
                    />
                </div>
            </template>
        </div>
    </q-page>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import {
    getDatasetConfig,
    getDatasetConfigs,
} from '@/core/api/dataset-configs';
import BinaryFeatureAiPanel from '@/modules/binary-feature-ae/components/BinaryFeatureAiPanel.vue';
import BinaryFeatureCompareCharts from '@/modules/binary-feature-ae/components/BinaryFeatureCompareCharts.vue';
import {
    postBinaryFeatureCalculate,
    postBinaryFeatureExplainRule,
} from '@/modules/binary-feature-ae/api';
import BinaryFeatureDetailCards from '@/modules/binary-feature-ae/components/BinaryFeatureDetailCards.vue';
import BinaryFeatureGrid from '@/modules/binary-feature-ae/components/BinaryFeatureGrid.vue';
import BinaryFeatureScatterPlot from '@/modules/binary-feature-ae/components/BinaryFeatureScatterPlot.vue';
import {
    BINARY_FEATURE_PERFORMANCE_TYPE,
    CI_LEVEL_OPTIONS,
    PERSPECTIVE_LABELS,
    PERSPECTIVE_OPTIONS,
    SIGNIFICANCE_OPTIONS,
} from '@/modules/binary-feature-ae/constants';
import type {
    ApiBinaryFeatureAiResponse,
    ApiBinaryFeatureCalculateResponse,
    ApiBinaryFeatureRow,
    BinaryFeatureCiLevel,
    BinaryFeaturePerspective,
    BinaryFeatureSignificance,
} from '@/types/binary-feature-ae';
import {
    isBinaryFeatureDatasetConfig,
    type ApiDatasetConfig,
} from '@/types/dataset-config';
import {
    formatCurrency,
    formatPercentFromRatio,
    formatWholeNumber,
} from '@/utils/format';

const route = useRoute();

const configs = ref<ApiDatasetConfig[]>([]);
const configsLoading = ref(false);
const selectedConfigId = ref<string | null>(null);
const loading = ref(false);
const errorMsg = ref<string | null>(null);
const responseData = ref<ApiBinaryFeatureCalculateResponse | null>(null);
const activeDatasetName = ref<string | null>(null);
const aiExplainLoading = ref(false);
const aiExplainError = ref<string | null>(null);
const aiExplainResponse = ref<ApiBinaryFeatureAiResponse | null>(null);

const categories = ref<string[]>([]);
const significanceValues = ref<BinaryFeatureSignificance[]>([...SIGNIFICANCE_OPTIONS]);
const searchText = ref('');
const minHitCount = ref<number | null>(0);
const minClaimCount = ref<number | null>(5);
const perspective = ref<BinaryFeaturePerspective>('count');
const ciLevel = ref<BinaryFeatureCiLevel>('95');
const sizeBy = ref<'hit_count' | 'claim_count' | 'claim_amount'>('hit_count');
const yDisplayCap = ref(2.0);
const xDisplayCap = ref(100);

function clampX() {
    const n = Number(xDisplayCap.value);
    xDisplayCap.value = Math.min(100, Math.max(0, isNaN(n) ? 0 : n));
}

function clampY() {
    const n = Number(yDisplayCap.value);
    yDisplayCap.value = Math.min(5, Math.max(0, isNaN(n) ? 0 : n));
}

const selectedRowIds = ref<string[]>([]);
const focusedRowId = ref<string | null>(null);
const pinnedRuleKeys = ref<string[]>([]);

const activeConfig = ref<ApiDatasetConfig | null>(null);
let abortController: AbortController | null = null;
let explainAbortController: AbortController | null = null;
let configSelectionRequestId = 0;

const routeConfigId = computed(() => {
    const raw = route.query.config;
    return typeof raw === 'string' && raw.trim() ? raw : null;
});

const binaryConfigs = computed(() =>
    configs.value.filter((config) => config.module_id === 'binary_feature_ae'),
);

const selectedConfig = computed(() => {
    if (!selectedConfigId.value) {
        return null;
    }

    return (
        binaryConfigs.value.find((config) => config.id === selectedConfigId.value) ?? null
    );
});

const configOptions = computed(() =>
    binaryConfigs.value.map((config) => ({
        label: `${config.dataset_name} (${config.file_path})`,
        value: config.id,
    })),
);

const hasSavedConfigs = computed(() => configOptions.value.length > 0);

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

const ciLevelRadioOptions = CI_LEVEL_OPTIONS.map((value) => ({
    label: `${value}%`,
    value,
}));

const perspectiveOptions = PERSPECTIVE_OPTIONS.map((value) => ({
    label: PERSPECTIVE_LABELS[value],
    value,
}));

const displayedPerspective = computed<BinaryFeaturePerspective>(() => {
    return responseData.value?.perspective ?? perspective.value;
});

const perspectiveLabel = computed(() => PERSPECTIVE_LABELS[displayedPerspective.value]);

const sizeByOptions = computed(() => [
    { label: 'Hit Count', value: 'hit_count' },
    { label: 'Claim Count', value: 'claim_count' },
    { label: 'Claim Amount', value: 'claim_amount' },
]);

const rows = computed(() => responseData.value?.rows ?? []);

const rowsByRuleKey = computed(() => {
    return new Map(rows.value.map((row) => [row.rule_key, row]));
});

const focusedRow = computed(() => {
    if (!focusedRowId.value) {
        return null;
    }

    return rows.value.find((row) => row.row_id === focusedRowId.value) ?? null;
});

const isAiExplainStale = computed(() => {
    if (!aiExplainResponse.value || !responseData.value) {
        return false;
    }

    // Frontend stale detection treats state_fingerprint as the visible-view fingerprint.
    return aiExplainResponse.value.state_fingerprint !== responseData.value.state_fingerprint;
});

const selectedRows = computed(() => {
    return rows.value.filter((row) => selectedRowIds.value.includes(row.row_id));
});

const pinnedRules = computed(() => {
    return pinnedRuleKeys.value
        .map((ruleKey) => rowsByRuleKey.value.get(ruleKey) ?? null)
        .filter((row): row is ApiBinaryFeatureRow => row !== null);
});

const hasHiddenPins = computed(() => {
    return pinnedRuleKeys.value.length > pinnedRules.value.length;
});

const activeClaimMetricLabel = computed(() => {
    return displayedPerspective.value === 'count'
        ? 'Median Claim Count'
        : 'Median Claim Amount';
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

function resetDatasetState() {
    abortController?.abort();
    abortController = null;
    clearExplainState();
    loading.value = false;
    activeConfig.value = null;
    activeDatasetName.value = null;
    responseData.value = null;
    errorMsg.value = null;
    categories.value = [];
    significanceValues.value = [...SIGNIFICANCE_OPTIONS];
    searchText.value = '';
    minHitCount.value = 0;
    minClaimCount.value = 5;
    perspective.value = 'count';
    ciLevel.value = '95';
    sizeBy.value = 'hit_count';
    yDisplayCap.value = 2.0;
    xDisplayCap.value = 100;
    selectedRowIds.value = [];
    focusedRowId.value = null;
    pinnedRuleKeys.value = [];
}

function clearExplainState() {
    explainAbortController?.abort();
    explainAbortController = null;
    aiExplainLoading.value = false;
    aiExplainError.value = null;
    aiExplainResponse.value = null;
}

async function ensureBinaryFeatureConfig(configId: string) {
    const config = await getDatasetConfig(configId);
    if (!isBinaryFeatureDatasetConfig(config)) {
        throw new Error('Selected configuration is not a Binary Feature Mortality A/E config.');
    }

    if (config.performance_type !== BINARY_FEATURE_PERFORMANCE_TYPE) {
        throw new Error('Selected configuration uses an unexpected performance type.');
    }

    return config;
}

async function loadConfigs() {
    configsLoading.value = true;

    try {
        const result = await getDatasetConfigs();
        configs.value = result.configs;
    } catch (err) {
        console.error('Failed to load dataset configs:', err);
    } finally {
        configsLoading.value = false;
    }
}

async function handleSelectedConfigChange(configId: string | null) {
    const requestId = configSelectionRequestId + 1;
    configSelectionRequestId = requestId;
    resetDatasetState();

    if (!configId) {
        return;
    }

    try {
        const config = await ensureBinaryFeatureConfig(configId);
        if (requestId !== configSelectionRequestId) {
            return;
        }

        activeConfig.value = config;
        activeDatasetName.value = config.dataset_name;
    } catch (err) {
        if (requestId !== configSelectionRequestId) {
            return;
        }

        errorMsg.value = err instanceof Error ? err.message : String(err);
    }
}

async function loadData() {
    if (!selectedConfigId.value || !activeConfig.value) {
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
                config_id: activeConfig.value.id,
                perspective: perspective.value,
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

async function onExplainRule() {
    if (!activeConfig.value || !focusedRow.value) {
        return;
    }

    const explainedRowId = focusedRow.value.row_id;
    clearExplainState();
    explainAbortController = new AbortController();
    const signal = explainAbortController.signal;
    aiExplainLoading.value = true;

    try {
        aiExplainResponse.value = await postBinaryFeatureExplainRule(
            {
                config_id: activeConfig.value.id,
                perspective: perspective.value,
                ci_level: ciLevel.value,
                categories: categories.value,
                significance_values: significanceValues.value,
                search_text: debouncedSearchText.value || null,
                min_hit_count: debouncedMinHitCount.value,
                min_claim_count: debouncedMinClaimCount.value,
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
                ? 'Explain Rule endpoint was not found on the backend. Restart the FastAPI server on port 8000 so it loads the new /api/binary-feature-ae/ai/explain-rule route.'
                : message;
    } finally {
        if (!signal.aborted) {
            aiExplainLoading.value = false;
        }
    }
}

function pinFocusedRule() {
    if (!focusedRow.value) {
        return;
    }

    if (pinnedRuleKeys.value.includes(focusedRow.value.rule_key)) {
        return;
    }

    pinnedRuleKeys.value = [...pinnedRuleKeys.value, focusedRow.value.rule_key];
}

function clearPins() {
    pinnedRuleKeys.value = [];
}

function focusEvidenceRow(rowId: string) {
    if (!rows.value.some((row) => row.row_id === rowId)) {
        return;
    }

    focusedRowId.value = rowId;
}

watch(
    () => routeConfigId.value,
    (configId) => {
        selectedConfigId.value = configId;
    },
    { immediate: true },
);

watch(
    () => [selectedConfigId.value, focusedRowId.value],
    () => {
        clearExplainState();
    },
);

watch(
    () => selectedConfigId.value,
    (configId) => {
        void handleSelectedConfigChange(configId);
    },
    { immediate: true },
);

watch(
    () => [
        selectedConfigId.value,
        activeConfig.value?.id,
        categories.value,
        significanceValues.value,
        perspective.value,
        ciLevel.value,
        debouncedSearchText.value,
        debouncedMinHitCount.value,
        debouncedMinClaimCount.value,
    ],
    () => {
        if (!selectedConfigId.value || !activeConfig.value) {
            return;
        }

        void loadData();
    },
    { deep: true },
);

watch(
    () => perspective.value,
    (nextPerspective) => {
        sizeBy.value = nextPerspective === 'amount' ? 'claim_amount' : 'hit_count';
    },
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
    void loadConfigs();
});

onBeforeUnmount(() => {
    abortController?.abort();
    explainAbortController?.abort();
});
</script>

<style scoped>
.page-shell {
    max-width: 100%;
}

.input-600 {
    width: 600px;
    max-width: 100%;
}

/* Filter card */
.filter-card {
    background: #fafafa;
    border: 1px solid #e3e3e3;
    border-radius: 10px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

/* Subtle grouping sub-panels inside the filter card */
.filter-group {
    background: #ffffff;
    border: 1px solid #ebebeb;
    border-radius: 6px;
    padding: 10px 12px;
}

.filter-group-label {
    font-weight: 500;
    letter-spacing: 0.01em;
}

/* Option group (radio + checkbox) spacing */
.filter-option-group :deep(.q-radio),
.filter-option-group :deep(.q-checkbox) {
    margin-right: 16px;
}

.filter-option-group :deep(.q-radio__label),
.filter-option-group :deep(.q-checkbox__label) {
    font-size: 0.85rem;
    color: #374151;
}

/* Section cards */
.section-card {
    border: 1px solid #dde2ea;
    border-radius: 8px;
    box-shadow: 0 1px 5px rgba(0, 0, 0, 0.06);
}

/* KPI metric cards */
.kpi-grid {
    display: grid;
    gap: 12px;
    grid-template-columns: repeat(7, minmax(150px, 1fr));
}

.kpi-card {
    min-height: 108px;
    border: 1px solid #dde2ea;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
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
