<template>
    <div ref="plotEl" class="binary-feature-plot"></div>
</template>

<script setup lang="ts">
import Plotly from 'plotly.js-dist-min';
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';

import type { ApiBinaryFeatureRow } from '@/types/binary-feature-ae';

import {
    CONFIDENCE_BAND_COLORS,
    CONFIDENCE_BAND_ORDER,
} from '@/modules/binary-feature-ae/constants';

const props = defineProps<{
    rows: ApiBinaryFeatureRow[];
    perspective: 'count' | 'amount';
    sizeBy: 'hit_count' | 'claim_count' | 'claim_amount';
    displayCap: number;
    xDisplayCap: number;
    selectedRowIds: string[];
    focusedRowId: string | null;
}>();

const emit = defineEmits<{
    'update:selectedRowIds': [value: string[]];
    'focus-row': [rowId: string];
}>();

const plotEl = ref<HTMLDivElement | null>(null);

function buildEmptyFigure(message: string) {
    return {
        data: [],
        layout: {
            template: 'plotly_white',
            height: 650,
            margin: { l: 60, r: 30, t: 70, b: 60 },
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

function markerSizeForRow(row: ApiBinaryFeatureRow, maxSizeValue: number): number {
    const sizeValue = Math.max(0, row[props.sizeBy] ?? 0);
    return Math.sqrt(sizeValue / Math.max(maxSizeValue, 1)) * 40 + 8;
}

function getPerspectiveLabel(): string {
    return props.perspective === 'count' ? 'Count' : 'Amount';
}

async function renderPlot() {
    const el = plotEl.value as any;
    if (!el) {
        return;
    }

    if (!props.rows.length) {
        const empty = buildEmptyFigure('No rules match the current filters.');
        await Plotly.react(el, empty.data, empty.layout, { responsive: true });
        return;
    }

    const maxSizeValue = Math.max(
        ...props.rows.map((row) => Number(row[props.sizeBy] ?? 0)),
        1,
    );

    const traces: any[] = [];

    for (const band of CONFIDENCE_BAND_ORDER) {
        const bandRows = props.rows.filter((row) => row.confidence_band === band);

        if (!bandRows.length) {
            // Add an empty trace so the band always appears in the legend
            traces.push({
                type: 'scatter',
                mode: 'markers',
                name: band,
                legendgroup: band,
                showlegend: true,
                x: [],
                y: [],
                marker: { color: CONFIDENCE_BAND_COLORS[band] },
                hoverinfo: 'skip',
            });
            continue;
        }

        const selectedpoints =
            props.selectedRowIds.length > 0
                ? bandRows
                      .map((row, index) =>
                          props.selectedRowIds.includes(row.row_id) ? index : -1,
                      )
                      .filter((index) => index >= 0)
                : undefined;

        traces.push({
            type: 'scatter',
            mode: 'markers',
            name: band,
            legendgroup: band,
            showlegend: true,
            x: bandRows.map((row) => row.hit_rate),
            y: bandRows.map((row) => Math.min(row.ae_ratio, props.displayCap)),
            customdata: bandRows.map((row) => [
                row.row_id,
                row.rule,
                row.RuleName,
                row.category,
                row.hit_count,
                row.hit_rate,
                row.claim_count,
                row.mec_sum,
                row.ae_ratio,
                row.ci_lower,
                row.ci_upper,
                row.significance_class,
                row.dominant_cola,
                row.dominant_cola_pct,
                row.confidence_band,
                row.claim_amount,
            ]),
            marker: {
                size: bandRows.map((row) => markerSizeForRow(row, maxSizeValue)),
                color: CONFIDENCE_BAND_COLORS[band],
                line: {
                    width: 0.5,
                    color: 'gray',
                },
                opacity: 0.88,
            },
            selectedpoints,
            selected: {
                marker: {
                    opacity: 1,
                    line: {
                        width: 1.5,
                        color: '#111827',
                    },
                },
            },
            unselected: {
                marker: {
                    opacity: props.selectedRowIds.length > 0 ? 0.18 : 0.88,
                },
            },
            hovertemplate:
                '<b>%{customdata[1]}</b><br>' +
                'Rule Name: %{customdata[2]}<br>' +
                'Category: %{customdata[3]}<br>' +
                'Hit Count: %{customdata[4]:,.0f}<br>' +
                'Hit Rate: %{customdata[5]:.4%}<br>' +
                'Claim Count: %{customdata[6]:,.0f}<br>' +
                'Claim Amount: %{customdata[15]:$,.0f}<br>' +
                'MEC Sum: %{customdata[7]:,.2f}<br>' +
                `${getPerspectiveLabel()} A/E Ratio: %{customdata[8]:.4f}<br>` +
                'CI: [%{customdata[9]:.4f}, %{customdata[10]:.4f}]<br>' +
                'Significance: %{customdata[11]}<br>' +
                `${getPerspectiveLabel()} Mix: %{customdata[12]} (%{customdata[13]:.1f}%)<br>` +
                'Confidence Band: %{customdata[14]}' +
                '<extra></extra>',
        });
    }

    if (props.focusedRowId) {
        const focusedRow = props.rows.find((row) => row.row_id === props.focusedRowId);
        if (focusedRow) {
            traces.push({
                type: 'scatter',
                mode: 'markers',
                name: 'Focused',
                showlegend: false,
                x: [focusedRow.hit_rate],
                y: [Math.min(focusedRow.ae_ratio, props.displayCap)],
                marker: {
                    size: markerSizeForRow(focusedRow, maxSizeValue) + 8,
                    color: 'rgba(0,0,0,0)',
                    line: {
                        width: 3,
                        color: '#111827',
                    },
                },
                hoverinfo: 'skip',
            });
        }
    }

    await Plotly.react(
        el,
        traces,
        {
            template: 'plotly_white',
            title: {
                text: `Binary Feature Triage Scatter (${getPerspectiveLabel()} Perspective)`,
                x: 0.5,
            },
            xaxis: { title: 'Hit Rate', tickformat: '.2%', range: [0, props.xDisplayCap / 100] },
            yaxis: {
                title: `A/E Ratio (${getPerspectiveLabel()})`,
                range: [0, props.displayCap],
            },
            height: 650,
            margin: { l: 60, r: 30, t: 70, b: 60 },
            dragmode: 'lasso',
            clickmode: 'event+select',
            uirevision: 'binary-feature-scatter',
            legend: { title: { text: 'Confidence Band' } },
            shapes: [
                {
                    type: 'line',
                    x0: 0,
                    x1: 1,
                    xref: 'paper',
                    y0: 1,
                    y1: 1,
                    yref: 'y',
                    line: { dash: 'dash', color: 'gray' },
                },
            ],
        },
        {
            responsive: true,
            displayModeBar: true,
        },
    );

    el.removeAllListeners?.('plotly_selected');
    el.removeAllListeners?.('plotly_deselect');
    el.removeAllListeners?.('plotly_click');

    el.on('plotly_selected', (event: any) => {
        const ids = (event?.points ?? [])
            .map((point: any) => point?.customdata?.[0])
            .filter((value: unknown): value is string => typeof value === 'string');
        emit('update:selectedRowIds', ids);
    });

    el.on('plotly_deselect', () => {
        emit('update:selectedRowIds', []);
    });

    el.on('plotly_click', (event: any) => {
        const rowId = event?.points?.[0]?.customdata?.[0];
        if (typeof rowId === 'string') {
            emit('focus-row', rowId);
        }
    });
}

onMounted(() => {
    void renderPlot();
});

watch(
    () => [
        props.rows,
        props.perspective,
        props.sizeBy,
        props.displayCap,
        props.xDisplayCap,
        props.selectedRowIds,
        props.focusedRowId,
    ],
    () => {
        void renderPlot();
    },
    { deep: true },
);

onBeforeUnmount(() => {
    const el = plotEl.value as any;
    if (el) {
        Plotly.purge(el);
    }
});
</script>

<style scoped>
.binary-feature-plot {
    width: 100%;
    min-height: 650px;
}
</style>
