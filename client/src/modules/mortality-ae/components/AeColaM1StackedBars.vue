<template>
    <div class="cola-chart">
        <div ref="plotlyDiv" class="cola-plotly-container"></div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import Plotly from 'plotly.js-dist-min';
import type { ApiAeColaM1StackedResults } from '@/modules/mortality-ae/types';

const props = defineProps<{
    data: ApiAeColaM1StackedResults;
}>();

const plotlyDiv = ref<HTMLDivElement | null>(null);

const palette = [
    '#1f77b4',
    '#ff7f0e',
    '#2ca02c',
    '#d62728',
    '#9467bd',
    '#8c564b',
    '#e377c2',
    '#7f7f7f',
    '#bcbd22',
    '#17becf',
    '#4e79a7',
    '#f28e2b',
    '#59a14f',
    '#e15759',
    '#b07aa1',
    '#9c755f',
    '#edc948',
    '#76b7b2',
];

function colorForCause(idx: number, cause: string): string {
    if ((cause || '').toLowerCase() === 'other') return '#9e9e9e';
    return palette[idx % palette.length] ?? '#1f77b4';
}

function createPlot() {
    if (!plotlyDiv.value || !props.data) return;

    const rows = props.data.rows ?? [];
    const causes = props.data.causes ?? [];
    if (rows.length === 0) return;

    const xGroups = rows.map((r) => r.x_group);

    // Create traces for each cause
    const traces: any[] = [];

    // Deaths count (subplot 1, row 1, col 1)
    causes.forEach((cause, idx) => {
        const yValues = rows.map((r) => Number(r.deaths_by_m1?.[cause] ?? 0) || 0);
        traces.push({
            x: xGroups,
            y: yValues,
            name: cause,
            type: 'bar',
            marker: { color: colorForCause(idx, cause) },
            xaxis: 'x1',
            yaxis: 'y1',
            legendgroup: cause,
            showlegend: true,
        });
    });

    // Deaths % (subplot 2, row 2, col 1)
    causes.forEach((cause, idx) => {
        const yValues = rows.map((r) => {
            const deaths = Number(r.deaths_by_m1?.[cause] ?? 0) || 0;
            const total = Number(r.total_deaths) || 0;
            return total > 0 ? (deaths / total) * 100 : 0;
        });
        traces.push({
            x: xGroups,
            y: yValues,
            name: cause,
            type: 'bar',
            marker: { color: colorForCause(idx, cause) },
            xaxis: 'x2',
            yaxis: 'y2',
            legendgroup: cause,
            showlegend: false,
        });
    });

    // Claims amount (subplot 3, row 1, col 2)
    causes.forEach((cause, idx) => {
        const yValues = rows.map((r) => Number(r.amounts_by_m1?.[cause] ?? 0) || 0);
        traces.push({
            x: xGroups,
            y: yValues,
            name: cause,
            type: 'bar',
            marker: { color: colorForCause(idx, cause) },
            xaxis: 'x3',
            yaxis: 'y3',
            legendgroup: cause,
            showlegend: false,
        });
    });

    // Claims % (subplot 4, row 2, col 2)
    causes.forEach((cause, idx) => {
        const yValues = rows.map((r) => {
            const amount = Number(r.amounts_by_m1?.[cause] ?? 0) || 0;
            const total = Number(r.total_amount) || 0;
            return total > 0 ? (amount / total) * 100 : 0;
        });
        traces.push({
            x: xGroups,
            y: yValues,
            name: cause,
            type: 'bar',
            marker: { color: colorForCause(idx, cause) },
            xaxis: 'x4',
            yaxis: 'y4',
            legendgroup: cause,
            showlegend: false,
        });
    });

    const layout: any = {
        grid: {
            rows: 1,
            columns: 4,
            pattern: 'independent',
        },
        barmode: 'stack',
        height: 500,
        margin: { t: 60, b: 80, l: 60, r: 40 },
        showlegend: true,
        legend: {
            orientation: 'h',
            yanchor: 'bottom',
            y: 1.15,
            xanchor: 'center',
            x: 0.5,
        },
        annotations: [
            {
                text: 'Deaths counts',
                xref: 'paper',
                yref: 'paper',
                x: 0.11875,
                y: 1.05,
                xanchor: 'center',
                yanchor: 'bottom',
                showarrow: false,
                font: { size: 13 },
            },
            {
                text: 'Deaths %',
                xref: 'paper',
                yref: 'paper',
                x: 0.38125,
                y: 1.05,
                xanchor: 'center',
                yanchor: 'bottom',
                showarrow: false,
                font: { size: 13 },
            },
            {
                text: 'Claims amounts',
                xref: 'paper',
                yref: 'paper',
                x: 0.61875,
                y: 1.05,
                xanchor: 'center',
                yanchor: 'bottom',
                showarrow: false,
                font: { size: 13 },
            },
            {
                text: 'Claims %',
                xref: 'paper',
                yref: 'paper',
                x: 0.88125,
                y: 1.05,
                xanchor: 'center',
                yanchor: 'bottom',
                showarrow: false,
                font: { size: 13 },
            },
        ],
        xaxis1: { domain: [0, 0.2375] },
        yaxis1: { domain: [0, 1], anchor: 'x1' },
        xaxis2: { domain: [0.2625, 0.487] },
        yaxis2: { domain: [0, 1], anchor: 'x2', ticksuffix: '%' },
        xaxis3: { domain: [0.512, 0.75] },
        yaxis3: { domain: [0, 1], anchor: 'x3' },
        xaxis4: { domain: [0.775, 1] },
        yaxis4: { domain: [0, 1], anchor: 'x4', ticksuffix: '%' },
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
    };

    Plotly.newPlot(plotlyDiv.value, traces, layout, config);
}

watch(() => props.data, () => {
    nextTick(() => createPlot());
}, { deep: true });

onMounted(() => {
    nextTick(() => createPlot());
});
</script>

<style scoped>
.cola-chart {
    width: 100%;
}

.cola-plotly-container {
    width: 100%;
    min-height: 500px;
}
</style>
