<template>
    <div class="column q-gutter-md">
        <q-card v-if="props.showSummary" flat bordered>
            <q-card-section v-if="focusedRow">
                <div class="text-h6">{{ focusedRow.rule }}</div>
                <div class="text-body1 text-grey-8 q-mt-xs">
                    {{ focusedRow.RuleName }}
                </div>
                <q-badge color="grey-8" class="q-mt-sm">
                    {{ focusedRow.significance_class }}
                </q-badge>
                <q-banner class="bg-grey-2 text-grey-9 q-mt-md" rounded dense>
                    {{ ruleInsight }}
                </q-banner>

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
                        <span class="detail-label">MEC Sum</span>
                        <span>{{ focusedRow.mec_sum.toFixed(2) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">A/E Ratio</span>
                        <span>{{ focusedRow.ae_ratio.toFixed(4) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">CI Lower ({{ ciLevel }}%)</span>
                        <span>{{ focusedRow.ci_lower.toFixed(4) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">CI Upper ({{ ciLevel }}%)</span>
                        <span>{{ focusedRow.ci_upper.toFixed(4) }}</span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">Dominant Claim Mix</span>
                        <span>
                            {{ focusedRow.dominant_cola }}
                            ({{ focusedRow.dominant_cola_pct.toFixed(1) }}%)
                        </span>
                    </div>
                    <div class="detail-metric">
                        <span class="detail-label">Impact Score</span>
                        <span>{{ focusedRow.impact_score.toFixed(4) }}</span>
                    </div>
                </div>
            </q-card-section>

            <q-card-section v-else>
                Click a point in the scatter or select a row in the table to inspect one rule.
            </q-card-section>
        </q-card>

        <div v-if="props.showCharts" class="row q-col-gutter-md">
            <div class="col-12 col-md-6">
                <q-card flat bordered>
                    <q-card-section>
                        <div ref="ciChartEl" class="mini-chart"></div>
                    </q-card-section>
                </q-card>
            </div>
            <div class="col-12 col-md-6">
                <q-card flat bordered>
                    <q-card-section>
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
    formatPercentFromRatio,
    formatWholeNumber,
} from '@/utils/format';

import { COLA_DEFINITIONS } from '@/modules/binary-feature-ae/constants';

const props = withDefaults(defineProps<{
    rows: ApiBinaryFeatureRow[];
    focusedRowId: string | null;
    ciLevel: '95' | '90' | '80';
    showSummary?: boolean;
    showCharts?: boolean;
}>(), {
    showSummary: true,
    showCharts: true,
});

const ciChartEl = ref<HTMLDivElement | null>(null);
const mixChartEl = ref<HTMLDivElement | null>(null);

const focusedRow = computed(() => {
    if (!props.focusedRowId) {
        return null;
    }
    return props.rows.find((row) => row.row_id === props.focusedRowId) ?? null;
});

const ruleInsight = computed(() => {
    const row = focusedRow.value;
    if (!row) {
        return '';
    }

    const hitValues = props.rows.map((item) => item.hit_count).sort((a, b) => a - b);
    const claimValues = props.rows.map((item) => item.claim_count).sort((a, b) => a - b);
    const widthValues = props.rows.map((item) => item.ci_width).sort((a, b) => a - b);

    const quantile = (values: number[], q: number) => {
        if (!values.length) return 0;
        const index = Math.min(
            values.length - 1,
            Math.max(0, Math.floor((values.length - 1) * q)),
        );
        return values[index];
    };

    const hitP75 = quantile(hitValues, 0.75);
    const claimP75 = quantile(claimValues, 0.75);
    const ciWidthP75 = quantile(widthValues, 0.75);

    const signal =
        row.ci_lower > 1
            ? 'Statistically elevated above expected.'
            : row.ci_upper < 1
              ? 'Statistically below expected.'
              : 'Not clearly different from expected; the confidence interval crosses 1.0.';

    const scale =
        row.hit_count >= hitP75 || row.claim_count >= claimP75
            ? 'Material scale relative to the rest of the visible rules.'
            : 'Lower-volume rule; interpret the ratio with some caution.';

    const stability =
        row.ci_width >= ciWidthP75
            ? 'Uncertainty is relatively wide.'
            : 'Confidence interval is relatively tighter.';

    const mix =
        row.dominant_cola_pct >= 50
            ? `Claim mix is concentrated in ${row.dominant_cola}.`
            : `Claim mix is more balanced, though ${row.dominant_cola} is the largest component.`;

    return `${signal} ${scale} ${stability} ${mix}`;
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
    await Plotly.react(
        ciEl,
        [
            {
                type: 'scatter',
                x: [ciLow, ciHigh],
                y: [row.rule, row.rule],
                mode: 'lines',
                line: { width: 6, color: '#4f46e5' },
                hoverinfo: 'skip',
                showlegend: false,
            },
            {
                type: 'scatter',
                x: [row.ae_ratio],
                y: [row.rule],
                mode: 'markers',
                marker: {
                    size: 12,
                    line: { width: 1, color: 'black' },
                    color: '#111827',
                },
                hovertemplate:
                    `A/E: ${row.ae_ratio.toFixed(4)}<br>` +
                    `CI: [${ciLow.toFixed(4)}, ${ciHigh.toFixed(4)}]` +
                    '<extra></extra>',
                showlegend: false,
            },
        ],
        {
            template: 'plotly_white',
            title: 'Selected Rule: A/E Confidence Interval',
            height: 260,
            margin: { l: 40, r: 20, t: 50, b: 40 },
            xaxis: {
                title: 'A/E Ratio',
                range: [Math.max(0, Math.min(ciLow, row.ae_ratio, 1) - 0.1), Math.max(ciHigh, row.ae_ratio, 1) + 0.1],
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
            y: [row.rule],
            x: [row[`${cola.key}_display` as keyof ApiBinaryFeatureRow] as number],
            name: cola.label,
            hovertemplate:
                `<b>${row.rule}</b><br>` +
                `Rule Name: ${row.RuleName}<br>` +
                `Category: ${row.category}<br>` +
                `A/E Ratio: ${row.ae_ratio.toFixed(4)}<br>` +
                `Significance: ${row.significance_class}<br>` +
                `Share: %{x:.1f}%` +
                '<extra></extra>',
        })),
        {
            template: 'plotly_white',
            title: 'Selected Rule: Claim Mix (Share %)',
            barmode: 'stack',
            height: 260,
            margin: { l: 20, r: 20, t: 50, b: 90 },
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
    () => [props.rows, props.focusedRowId, props.ciLevel],
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
</style>
