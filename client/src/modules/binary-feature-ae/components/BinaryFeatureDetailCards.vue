<template>
    <div class="column">
        <q-card v-if="props.showSummary" flat bordered>
            <q-card-section v-if="focusedRow">
                <div class="text-h6">{{ focusedRow.rule }}</div>
                <div class="text-body1 text-grey-8 q-mt-xs">
                    {{ focusedRow.RuleName }}
                </div>
                <q-badge color="grey-8" class="q-mt-sm">
                    {{ focusedRow.significance_class }}
                </q-badge>

                <div class="detail-metrics q-mt-md">
                    <div class="detail-metric">
                        <span class="detail-label">Category</span>
                        <span>{{ focusedRow.category }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">Hit Count</span>
                        <span>{{ formatWholeNumber(focusedRow.hit_count) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">Hit Rate</span>
                        <span>{{ formatPercentFromRatio(focusedRow.hit_rate) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">Claim Count</span>
                        <span>{{ formatWholeNumber(focusedRow.claim_count) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">Claim Amount</span>
                        <span>{{ formatCurrency(focusedRow.claim_amount) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">MEC Sum</span>
                        <span>{{ focusedRow.mec_sum.toFixed(2) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">MEN Sum</span>
                        <span>{{ formatCurrency(focusedRow.men_sum) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">A/E Ratio ({{ perspectiveLabel }})</span>
                        <span>{{ focusedRow.ae_ratio.toFixed(4) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">
                            CI Lower ({{ perspectiveLabel }} {{ ciLevel }}%)
                        </span>
                        <span>{{ focusedRow.ci_lower.toFixed(4) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">
                            CI Upper ({{ perspectiveLabel }} {{ ciLevel }}%)
                        </span>
                        <span>{{ focusedRow.ci_upper.toFixed(4) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">
                            Dominant {{ perspectiveLabel }} Claim Mix
                        </span>
                        <span>
                            {{ focusedRow.dominant_cola }}
                            ({{ focusedRow.dominant_cola_pct.toFixed(1) }}%)
                        </span>
                    </div>
                </div>
            </q-card-section>

            <q-card-section v-else>
                Click a point in the scatter or select a row in the table to inspect one rule.
            </q-card-section>
        </q-card>

        <div
            v-if="props.showCharts"
            class="row q-col-gutter-md"
            :class="{ 'q-mt-md': props.showSummary }"
        >
            <div class="col-12 col-md-6">
                <q-card flat bordered>
                    <q-card-section>
                        <div
                            v-if="focusedRow"
                            class="text-caption text-grey-7 q-mb-xs chart-rule-subtitle"
                        >
                            {{ focusedRow.RuleName }}
                        </div>
                        <div ref="ciChartEl" class="mini-chart"></div>
                    </q-card-section>
                </q-card>
            </div>
            <div class="col-12 col-md-6">
                <q-card flat bordered>
                    <q-card-section>
                        <div
                            v-if="focusedRow"
                            class="text-caption text-grey-7 q-mb-xs chart-rule-subtitle"
                        >
                            {{ focusedRow.RuleName }}
                        </div>
                        <div ref="mixChartEl" class="mini-chart"></div>
                    </q-card-section>
                </q-card>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import Plotly from 'plotly.js-dist-min';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import type { ApiBinaryFeatureRow } from '@/types/binary-feature-ae';
import {
    formatCurrency,
    formatPercentFromRatio,
    formatWholeNumber,
    truncateLabel,
} from '@/utils/format';

import { COLA_DEFINITIONS } from '@/modules/binary-feature-ae/constants';

const props = withDefaults(
    defineProps<{
        rows: ApiBinaryFeatureRow[];
        perspective: 'count' | 'amount';
        focusedRowId: string | null;
        ciLevel: '95' | '90' | '80';
        showSummary?: boolean;
        showCharts?: boolean;
    }>(),
    {
        showSummary: true,
        showCharts: true,
    },
);

const ciChartEl = ref<HTMLDivElement | null>(null);
const mixChartEl = ref<HTMLDivElement | null>(null);

const focusedRow = computed(() => {
    if (!props.focusedRowId) {
        return null;
    }
    return props.rows.find((row) => row.row_id === props.focusedRowId) ?? null;
});

const perspectiveLabel = computed(() => {
    return props.perspective === 'count' ? 'Count' : 'Amount';
});

function buildEmptyFigure(message: string, height = 260) {
    return {
        data: [],
        layout: {
            template: 'plotly_white',
            height,
            margin: { l: 40, r: 20, t: 50, b: 40 },
            xaxis: { visible: false },
            yaxis: { visible: false },
            annotations: [
                {
                    text: message,
                    x: 0.5,
                    y: 0.5,
                    xref: 'paper',
                    yref: 'paper',
                    showarrow: false,
                    font: { size: 16 },
                },
            ],
        },
    };
}

async function renderCharts() {
    const ciEl = ciChartEl.value as any;
    const mixEl = mixChartEl.value as any;
    const row = focusedRow.value;

    if (!ciEl || !mixEl) {
        return;
    }

    if (!row) {
        const emptyCi = buildEmptyFigure('Select one rule to see its CI.', 260);
        const emptyMix = buildEmptyFigure('Select one rule to see its claim mix.', 260);
        await Plotly.react(ciEl, emptyCi.data, emptyCi.layout, { responsive: true });
        await Plotly.react(mixEl, emptyMix.data, emptyMix.layout, { responsive: true });
        return;
    }

    const ciLow = row.ci_lower;
    const ciHigh = row.ci_upper;
    const truncatedRule = truncateLabel(row.rule);
    await Plotly.react(
        ciEl,
        [
            {
                type: 'scatter',
                x: [ciLow, ciHigh],
                y: [truncatedRule, truncatedRule],
                mode: 'lines',
                line: { width: 6, color: '#4f46e5' },
                hoverinfo: 'skip',
                showlegend: false,
            },
            {
                type: 'scatter',
                x: [row.ae_ratio],
                y: [truncatedRule],
                mode: 'markers',
                marker: {
                    size: 12,
                    line: { width: 1, color: 'black' },
                    color: '#111827',
                },
                hovertemplate:
                    `<b>${row.rule}</b><br>` +
                    `${row.RuleName}<br>` +
                    `Claim Count: ${row.claim_count.toLocaleString()}<br>` +
                    `Claim Amount: ${formatCurrency(row.claim_amount)}<br>` +
                    `MEC Sum: ${row.mec_sum.toFixed(2)}<br>` +
                    `MEN Sum: ${formatCurrency(row.men_sum)}<br>` +
                    `${perspectiveLabel.value} A/E: ${row.ae_ratio.toFixed(4)}<br>` +
                    `CI: [${ciLow.toFixed(4)}, ${ciHigh.toFixed(4)}]` +
                    '<extra></extra>',
                showlegend: false,
            },
        ],
        {
            template: 'plotly_white',
            title: `Selected Rule: ${perspectiveLabel.value} A/E Confidence Interval`,
            height: 260,
            margin: { l: 90, r: 20, t: 50, b: 40 },
            xaxis: {
                title: `A/E Ratio (${perspectiveLabel.value})`,
                range: [
                    Math.max(0, Math.min(ciLow, row.ae_ratio, 1) - 0.1),
                    Math.max(ciHigh, row.ae_ratio, 1) + 0.1,
                ],
            },
            yaxis: { title: '' },
            shapes: [
                {
                    type: 'line',
                    x0: 1,
                    x1: 1,
                    y0: 0,
                    y1: 1,
                    yref: 'paper',
                    line: { dash: 'dash', color: 'gray' },
                },
            ],
        },
        { responsive: true },
    );

    await Plotly.react(
        mixEl,
        COLA_DEFINITIONS.map((cola) => ({
            type: 'bar',
            orientation: 'h',
            y: [truncatedRule],
            x: [row[`${cola.key}_display` as keyof ApiBinaryFeatureRow] as number],
            name: cola.label,
            hovertemplate:
                `<b>${row.rule}</b><br>` +
                `Rule Name: ${row.RuleName}<br>` +
                `Category: ${row.category}<br>` +
                `${perspectiveLabel.value} A/E Ratio: ${row.ae_ratio.toFixed(4)}<br>` +
                `Significance: ${row.significance_class}<br>` +
                `Claim Count: ${row.claim_count.toLocaleString()}<br>` +
                `Claim Amount: ${formatCurrency(row.claim_amount)}<br>` +
                `MEC Sum: ${row.mec_sum.toFixed(2)}<br>` +
                `MEN Sum: ${formatCurrency(row.men_sum)}<br>` +
                `Share: %{x:.1f}%` +
                '<extra></extra>',
        })),
        {
            template: 'plotly_white',
            title: `Selected Rule: Claim Mix (${perspectiveLabel.value} Share %)`,
            barmode: 'stack',
            height: 260,
            margin: { l: 90, r: 20, t: 50, b: 40 },
            xaxis: { title: '' },
            yaxis: { title: '' },
        },
        { responsive: true },
    );
}

onMounted(() => {
    void renderCharts();
});

watch(
    () => [props.rows, props.perspective, props.focusedRowId, props.ciLevel],
    () => {
        void renderCharts();
    },
    { deep: true },
);

onBeforeUnmount(() => {
    if (ciChartEl.value) {
        Plotly.purge(ciChartEl.value as any);
    }
    if (mixChartEl.value) {
        Plotly.purge(mixChartEl.value as any);
    }
});
</script>

<style scoped>
.detail-metrics {
    display: grid;
    gap: 8px;
}

.detail-metric {
    display: flex;
    justify-content: space-between;
    gap: 12px;
}

.detail-label {
    color: #616161;
    font-weight: 600;
}

.mini-chart {
    width: 100%;
    min-height: 260px;
}

.chart-rule-subtitle {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}
</style>
