<template>
    <q-card flat bordered class="insight-banner">
        <q-expansion-item
            v-model="expanded"
            dense
            dense-toggle
            expand-separator
            header-class="insight-header"
        >
            <template #header>
                <q-item-section>
                    <div class="text-h6">Diagnostic insights</div>
                    <div class="text-body2 text-grey-7">
                        Ranked 1D and 2D segments from the saved dataset configuration.
                    </div>
                </q-item-section>
                <q-item-section side class="items-end q-gutter-y-xs">
                    <q-chip dense color="grey-2" text-color="dark">DuckDB</q-chip>
                    <div class="text-caption text-grey-7">
                        {{ summaryText }}
                    </div>
                </q-item-section>
            </template>

            <q-tabs
                v-model="activeTab"
                dense
                align="left"
                active-color="primary"
                indicator-color="primary"
                class="bg-grey-1"
            >
                <q-tab name="count" label="Count" />
                <q-tab name="amount" label="Amount" />
            </q-tabs>

            <q-separator />

            <q-card-section v-if="loading" class="q-gutter-y-sm">
                <q-skeleton v-for="idx in 5" :key="idx" type="rect" height="42px" />
            </q-card-section>

            <q-banner v-else-if="error" class="bg-red-1 text-negative q-ma-md" dense>
                {{ error }}
            </q-banner>

            <q-banner
                v-else-if="activeRows.length === 0"
                class="bg-grey-1 text-grey-8 q-ma-md"
                dense
            >
                No {{ activeTab }} insights met the current signal thresholds.
            </q-banner>

            <q-markup-table v-else flat dense separator="horizontal" class="insight-table">
                <thead>
                    <tr>
                        <th class="text-left">Segment</th>
                        <th class="text-left">Dimensions</th>
                        <th class="text-right">Sample</th>
                        <th class="text-right">Actual</th>
                        <th class="text-right">Expected</th>
                        <th class="text-right">Variance</th>
                        <th class="text-right">A/E</th>
                        <th class="text-right">Action</th>
                    </tr>
                </thead>
                <tbody>
                    <tr
                        v-for="insight in activeRows"
                        :key="`${activeTab}-${insight.segment_label}`"
                        class="insight-row cursor-pointer"
                        @click="emit('apply', insight.drill)"
                    >
                        <td class="text-left">
                            <div class="text-weight-medium">{{ insight.segment_label }}</div>
                        </td>
                        <td class="text-left">
                            <div class="row q-col-gutter-xs">
                                <div
                                    v-for="dimension in insight.dimensions"
                                    :key="`${insight.segment_label}-${dimension}`"
                                    class="col-auto"
                                >
                                    <q-chip dense outline color="primary" text-color="primary">
                                        {{ dimension }}
                                    </q-chip>
                                </div>
                            </div>
                        </td>
                        <td class="text-right">{{ formatWholeNumber(insight.sample_size) }}</td>
                        <td class="text-right">{{ formatMetric(insight, 'actual') }}</td>
                        <td class="text-right">{{ formatMetric(insight, 'expected') }}</td>
                        <td class="text-right">
                            <span :class="varianceClass(insight)">
                                {{ formatMetric(insight, 'variance') }}
                            </span>
                        </td>
                        <td class="text-right">{{ formatAe(insight) }}</td>
                        <td class="text-right">
                            <q-btn
                                flat
                                dense
                                color="primary"
                                label="Drill"
                                @click.stop="emit('apply', insight.drill)"
                            />
                        </td>
                    </tr>
                </tbody>
            </q-markup-table>
        </q-expansion-item>
    </q-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

import type {
    ApiAeInsightDrill,
    ApiAeInsightResult,
    ApiAeInsightsResults,
} from '@/modules/mortality-ae/types';
import {
    formatCurrency,
    formatPercentFromRatio,
    formatWholeNumber,
} from '@/utils/format';

const props = defineProps<{
    insights: ApiAeInsightsResults | null;
    loading: boolean;
    error: string | null;
}>();

const emit = defineEmits<{
    apply: [drill: ApiAeInsightDrill];
}>();

const expanded = ref(true);
const activeTab = ref<'count' | 'amount'>('count');

const activeRows = computed<ApiAeInsightResult[]>(() => {
    if (!props.insights) return [];
    return activeTab.value === 'count'
        ? props.insights.count_insights
        : props.insights.amount_insights;
});

const summaryText = computed(() => {
    if (props.loading) return 'Loading insights';
    if (props.error) return 'Insights unavailable';
    const countTotal = props.insights?.count_insights.length ?? 0;
    const amountTotal = props.insights?.amount_insights.length ?? 0;
    return `${countTotal} count, ${amountTotal} amount`;
});

function formatMetric(
    insight: ApiAeInsightResult,
    metric: 'actual' | 'expected' | 'variance',
): string {
    if (activeTab.value === 'count') {
        const value =
            metric === 'actual'
                ? insight.actual_count
                : metric === 'expected'
                  ? insight.expected_count
                  : insight.variance_count;
        return formatWholeNumber(value);
    }

    const value =
        metric === 'actual'
            ? insight.actual_amount
            : metric === 'expected'
              ? insight.expected_amount
              : insight.variance_amount;
    return formatCurrency(value);
}

function formatAe(insight: ApiAeInsightResult): string {
    return formatPercentFromRatio(
        activeTab.value === 'count' ? insight.ae_count : insight.ae_amount,
    );
}

function varianceClass(insight: ApiAeInsightResult): string {
    const value =
        activeTab.value === 'count' ? insight.variance_count : insight.variance_amount;
    if (value > 0) return 'text-negative';
    if (value < 0) return 'text-positive';
    return '';
}
</script>

<style scoped>
.insight-banner {
    overflow: hidden;
}

.insight-header {
    align-items: flex-start;
}

.insight-table {
    font-size: 0.92rem;
}

.insight-row:hover {
    background: rgba(25, 118, 210, 0.06);
}
</style>
