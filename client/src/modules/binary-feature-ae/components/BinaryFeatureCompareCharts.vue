<template>
    <div class="row q-col-gutter-md">
        <div class="col-12 col-md-6">
            <q-card flat bordered>
                <q-card-section>
                    <div ref="ciChartEl" class="compare-chart"></div>
                </q-card-section>
            </q-card>
        </div>
        <div class="col-12 col-md-6">
            <q-card flat bordered>
                <q-card-section>
                    <div ref="mixChartEl" class="compare-chart"></div>
                </q-card-section>
            </q-card>
        </div>
    </div>
</template>

<script setup lang="ts">
import Plotly from 'plotly.js-dist-min';
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';

import type { ApiBinaryFeatureRow } from '@/types/binary-feature-ae';
import { truncateLabel } from '@/utils/format';

import { COLA_DEFINITIONS } from '@/modules/binary-feature-ae/constants';

const props = defineProps<{
    selectedRows: ApiBinaryFeatureRow[];
}>();

const ciChartEl = ref<HTMLDivElement | null>(null);
const mixChartEl = ref<HTMLDivElement | null>(null);

function buildEmptyFigure(message: string, height = 420) {
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
    if (!ciEl || !mixEl) {
        return;
    }

    if (!props.selectedRows.length) {
        const empty = buildEmptyFigure(
            'Select rows in the table or lasso points in the chart.',
        );
        await Plotly.react(ciEl, empty.data, empty.layout, { responsive: true });
        await Plotly.react(mixEl, empty.data, empty.layout, { responsive: true });
        return;
    }

    const sortedRows = [...props.selectedRows].sort((left, right) => {
        if (right.ae_ratio !== left.ae_ratio) {
            return right.ae_ratio - left.ae_ratio;
        }
        return right.claim_count - left.claim_count;
    });

    await Plotly.react(
        ciEl,
        [
            {
                type: 'scatter',
                x: sortedRows.map((row) => row.ae_ratio),
                y: sortedRows.map((row) => truncateLabel(row.rule)),
                mode: 'markers',
                error_x: {
                    type: 'data',
                    symmetric: false,
                    array: sortedRows.map((row) => row.ci_upper - row.ae_ratio),
                    arrayminus: sortedRows.map((row) => row.ae_ratio - row.ci_lower),
                    thickness: 1.4,
                    width: 0,
                },
                marker: {
                    size: 10,
                    line: { width: 1, color: 'black' },
                    color: '#2563eb',
                },
                customdata: sortedRows.map((row) => [
                    row.RuleName,
                    row.category,
                    row.claim_count,
                    row.hit_count,
                    row.significance_class,
                    row.rule,
                ]),
                hovertemplate:
                    '<b>%{customdata[5]}</b><br>' +
                    'Rule Name: %{customdata[0]}<br>' +
                    'Category: %{customdata[1]}<br>' +
                    'Claim Count: %{customdata[2]:,.0f}<br>' +
                    'Hit Count: %{customdata[3]:,.0f}<br>' +
                    'Significance: %{customdata[4]}<br>' +
                    'A/E: %{x:.4f}<extra></extra>',
                showlegend: false,
            },
        ],
        {
            template: 'plotly_white',
            title: 'Selected Rules: A/E with Confidence Intervals',
            height: Math.max(320, 120 + 30 * sortedRows.length),
            margin: { l: 90, r: 20, t: 50, b: 40 },
            xaxis: { title: 'A/E Ratio' },
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

    const mixRows = [...props.selectedRows].sort((left, right) => {
        if (left.ae_ratio !== right.ae_ratio) {
            return left.ae_ratio - right.ae_ratio;
        }
        return left.claim_count - right.claim_count;
    });

    await Plotly.react(
        mixEl,
        COLA_DEFINITIONS.map((cola) => ({
            type: 'bar',
            orientation: 'h',
            y: mixRows.map((row) => truncateLabel(row.rule)),
            x: mixRows.map(
                (row) => row[`${cola.key}_display` as keyof ApiBinaryFeatureRow] as number,
            ),
            name: cola.label,
            customdata: mixRows.map((row) => [
                row.RuleName,
                row.category,
                row.ae_ratio,
                row.significance_class,
                row.rule,
            ]),
            hovertemplate:
                '<b>%{customdata[4]}</b><br>' +
                'Rule Name: %{customdata[0]}<br>' +
                'Category: %{customdata[1]}<br>' +
                'A/E Ratio: %{customdata[2]:.4f}<br>' +
                'Significance: %{customdata[3]}<br>' +
                'Share: %{x:.1f}%<extra></extra>',
        })),
        {
            template: 'plotly_white',
            title: 'Selected Rules: Claim Mix (Share %)',
            barmode: 'stack',
            height: Math.max(320, 100 + 40 * mixRows.length),
            margin: { l: 90, r: 20, t: 50, b: 110 },
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
    () => props.selectedRows,
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
.compare-chart {
    width: 100%;
    min-height: 420px;
}
</style>
