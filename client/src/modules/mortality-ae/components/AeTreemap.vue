<template>
    <div class="treemap-wrapper">
        <div ref="plotEl" class="treemap-container"></div>
        <div v-if="legendItems.length" class="chart-legend">
            <div
                v-for="item in legendItems"
                :key="item.key"
                class="legend-item"
                :style="{ opacity: item.enabled ? 1 : 0.35 }"
                role="button"
                tabindex="0"
                @click="onLegendClick(item.key)"
                @keydown.enter.prevent="onLegendClick(item.key)"
            >
                <span class="swatch" :style="{ backgroundColor: item.color }"></span>
                <span class="label">{{ item.label }}</span>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import Plotly from 'plotly.js-dist-min';
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import type {
    ApiAeUnivariateRow,
    ApiAeUnivariateSplitResults,
} from '@/modules/mortality-ae/types';

const props = withDefaults(defineProps<{
    rows: ApiAeUnivariateRow[];
    metric: 'count' | 'amount';
    variableName: string;
    splitResults?: ApiAeUnivariateSplitResults[] | null;
    splitVariableName?: string | null;
    splitXAxisKind?: 'numeric' | 'date' | 'categorical' | null;
    showOverall?: boolean;
    splitVisible?: Record<string, boolean>;
}>(), {
    splitResults: null,
    splitVariableName: null,
    splitXAxisKind: null,
    showOverall: true,
    splitVisible: () => ({}),
});

const emit = defineEmits<{
    'update:showOverall': [value: boolean];
    'update:splitVisible': [value: Record<string, boolean>];
}>();

const plotEl = ref<HTMLDivElement | null>(null);

const hasSplits = computed(() => {
    return Boolean(props.splitResults && props.splitResults.length > 0);
});

const splitGroups = computed(() => {
    return (props.splitResults ?? []).map((s) => s.split_group);
});

function ensureSplitVisibility() {
    const next: Record<string, boolean> = { ...props.splitVisible };
    let changed = false;
    for (const g of splitGroups.value) {
        if (next[g] === undefined) {
            next[g] = false;
            changed = true;
        }
    }
    // drop stale keys
    for (const key of Object.keys(next)) {
        if (!splitGroups.value.includes(key)) {
            delete next[key];
            changed = true;
        }
    }
    if (changed) emit('update:splitVisible', next);
}

const legendItems = computed(() => {
    if (!hasSplits.value) return [];
    const items: Array<{ key: string; label: string; color: string; enabled: boolean }> = [];
    items.push({
        key: 'overall',
        label: 'Overall',
        color: 'rgba(25, 118, 210, 1)',
        enabled: props.showOverall,
    });
    const palette = [
        '#1b9e77',
        '#d95f02',
        '#7570b3',
        '#e7298a',
        '#66a61e',
        '#e6ab02',
        '#a6761d',
        '#666666',
        '#1f78b4',
        '#b15928',
    ];
    const groups = splitGroups.value;
    const splitName = (props.splitVariableName || '').trim();
    // Don't prefix categorical variables
    const prefix = (splitName && props.splitXAxisKind !== 'categorical') ? `${splitName} ` : '';
    for (let i = 0; i < groups.length; i++) {
        items.push({
            key: `split:${groups[i]}`,
            label: `${prefix}${groups[i]}`,
            color: palette[i % palette.length],
            enabled: Boolean(props.splitVisible[groups[i]]),
        });
    }
    return items;
});

function onLegendClick(key: string) {
    if (key === 'overall') {
        // Show overall, hide all splits
        emit('update:showOverall', true);
        const allHidden: Record<string, boolean> = {};
        for (const g of splitGroups.value) {
            allHidden[g] = false;
        }
        emit('update:splitVisible', allHidden);
        return;
    }
    if (!key.startsWith('split:')) return;
    const group = key.slice('split:'.length);
    ensureSplitVisibility();
    
    // Hide overall, toggle the clicked split
    emit('update:showOverall', false);
    emit('update:splitVisible', { ...props.splitVisible, [group]: !props.splitVisible[group] });
}

function getAeValue(row: ApiAeUnivariateRow): number | null {
    return props.metric === 'count' ? row.ae : row.ae_amount;
}

function getAreaValue(row: ApiAeUnivariateRow): number {
    // For count: use policy count (sample_size)
    // For amount: use total face amount
    return props.metric === 'count' ? row.sample_size : row.total_face_amount;
}

function getColorForAe(ae: number | null): string {
    if (ae === null || !Number.isFinite(ae)) return 'rgb(200, 200, 200)'; // Gray for invalid
    
    // Color scale:
    // ae >= 1.8: deep red
    // ae = 1.05: neutral (light yellow/beige)
    // ae = 0.7: deep green
    
    if (ae >= 1.05) {
        // Interpolate from neutral to red (1.05 → 1.8+)
        const t = Math.min((ae - 1.05) / (1.8 - 1.05), 1.0); // 0 to 1
        const r = Math.round(255);
        const g = Math.round(235 - t * 135); // 235 → 100
        const b = Math.round(180 - t * 80); // 180 → 100
        return `rgb(${r}, ${g}, ${b})`;
    } else {
        // Interpolate from green to neutral (0.7 → 1.05)
        const t = Math.min(Math.max((ae - 0.7) / (1.05 - 0.7), 0.0), 1.0); // 0 to 1
        const r = Math.round(100 + t * 155); // 100 → 255
        const g = Math.round(180 + t * 55); // 180 → 235
        const b = Math.round(100 + t * 80); // 100 → 180
        return `rgb(${r}, ${g}, ${b})`;
    }
}

function formatNumber(x: number, decimals: number): string {
    return Intl.NumberFormat(undefined, { 
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals 
    }).format(x * 100) + '%';
}

function renderTreemap() {
    const el = plotEl.value;
    if (!el) return;

    const labels: string[] = [];
    const parents: string[] = [];
    const values: number[] = [];
    const colors: string[] = [];
    const customdata: Array<{
        category: string;
        sampleSize: number;
        mac: number;
        mec: number;
        man: number;
        men: number;
        totalFaceAmount: number;
        ae: number | null;
        aeAmount: number | null;
    }> = [];
    const textLabels: string[] = [];

    // Root node
    labels.push('');
    parents.push('');
    values.push(0);
    colors.push('rgba(0,0,0,0)');
    customdata.push({
        category: '',
        sampleSize: 0,
        mac: 0,
        mec: 0,
        man: 0,
        men: 0,
        totalFaceAmount: 0,
        ae: null,
        aeAmount: null,
    });
    textLabels.push('');

    // Check which splits are visible
    const visibleSplits = (props.splitResults ?? []).filter(s => props.splitVisible[s.split_group]);
    
    if (!hasSplits.value || props.showOverall) {
        // No splits OR showing overall: show overall rows as direct children of root
        const overallRows = props.rows.filter(r => r.variable_group !== 'Total');
        
        for (const row of overallRows) {
            const ae = getAeValue(row);
            const area = getAreaValue(row);
            
            if (area <= 0) continue;
            
            labels.push(row.variable_group);
            parents.push(''); // Direct child of root
            values.push(area);
            colors.push(getColorForAe(ae));
            
            customdata.push({
                category: row.variable_group,
                sampleSize: row.sample_size,
                mac: row.deaths,
                mec: row.expected_count,
                man: row.actual_amount,
                men: row.expected_amount,
                totalFaceAmount: row.total_face_amount,
                ae: row.ae,
                aeAmount: row.ae_amount,
            });

            const aeText = ae !== null ? formatNumber(ae, 1) : '—';
            textLabels.push(`A/E: ${aeText}`);
        }
    } else if (visibleSplits.length > 0) {
        // Showing one or more split groups: create hierarchy
        const splitName = (props.splitVariableName || 'Split').trim();
        
        for (const splitResult of visibleSplits) {
            // Don't prefix categorical variables
            const splitGroupLabel = props.splitXAxisKind === 'categorical' 
                ? splitResult.split_group 
                : `${splitName}: ${splitResult.split_group}`;
            
            // Add parent node for this split group
            labels.push(splitGroupLabel);
            parents.push(''); // Child of root
            values.push(0); // Will be auto-calculated by Plotly
            colors.push('rgba(220, 220, 220, 0.3)'); // Light gray for parent
            customdata.push({
                category: splitGroupLabel,
                sampleSize: 0,
                mac: 0,
                mec: 0,
                man: 0,
                men: 0,
                totalFaceAmount: 0,
                ae: null,
                aeAmount: null,
            });
            textLabels.push(splitResult.split_group);
            
            // Add category rows as children of this split group
            const splitRows = splitResult.rows.filter(r => r.variable_group !== 'Total');
            
            for (const row of splitRows) {
                const ae = getAeValue(row);
                const area = getAreaValue(row);
                
                if (area <= 0) continue;
                
                // Make label unique by combining split group and category
                const uniqueLabel = `${splitGroupLabel} - ${row.variable_group}`;
                
                labels.push(uniqueLabel);
                parents.push(splitGroupLabel); // Child of this split group
                values.push(area);
                colors.push(getColorForAe(ae));
                
                customdata.push({
                    category: row.variable_group,
                    sampleSize: row.sample_size,
                    mac: row.deaths,
                    mec: row.expected_count,
                    man: row.actual_amount,
                    men: row.expected_amount,
                    totalFaceAmount: row.total_face_amount,
                    ae: row.ae,
                    aeAmount: row.ae_amount,
                });

                const aeText = ae !== null ? formatNumber(ae, 1) : '—';
                textLabels.push(`A/E: ${aeText}`);
            }
        }
    }
    
    if (labels.length <= 1) {
        // Only root node, nothing to display
        Plotly.purge(el);
        return;
    }

        const hovertemplate = props.metric === 'count'
                ? '<b>%{label}</b><br>' +
                    'Policy Count: %{customdata.sampleSize:,}<br>' +
                    'MAC: %{customdata.mac:.2f}<br>' +
                    'MEC: %{customdata.mec:.2f}<br>' +
                    'A/E: %{customdata.ae:.1%}<br>' +
                    '<extra></extra>'
                : '<b>%{label}</b><br>' +
                    'Total Face Amount: %{value:,.0f}<br>' +
                    'MAN: %{customdata.man:,.0f}<br>' +
                    'MEN: %{customdata.men:,.0f}<br>' +
                    'A/E: %{customdata.aeAmount:.1%}<br>' +
                    '<extra></extra>';

    const data: Partial<Plotly.PlotData>[] = [{
        type: 'treemap',
        labels: labels,
        parents: parents,
        values: values,
        text: textLabels,
        textposition: 'middle center',
        marker: {
            colors: colors,
            line: { width: 2, color: 'white' },
        },
        customdata: customdata,
        hovertemplate: hovertemplate,
        textfont: {
            size: 12,
            color: 'black',
            family: 'Arial, sans-serif',
        },
    }];

    const layout: Partial<Plotly.Layout> = {
        margin: { t: 0, l: 0, r: 0, b: 0 },
        height: 500,
    };

    const config: Partial<Plotly.Config> = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
    };

    Plotly.newPlot(el, data, layout, config);
}

onMounted(() => {
    renderTreemap();
});

onBeforeUnmount(() => {
    const el = plotEl.value;
    if (el) {
        Plotly.purge(el);
    }
});

watch(
    () => [props.rows, props.metric, props.variableName, props.showOverall, props.splitVisible, props.splitResults],
    () => {
        renderTreemap();
    },
    { deep: true },
);

watch(
    () => props.splitResults,
    () => {
        ensureSplitVisibility();
    },
    { immediate: true, deep: true },
);
</script>

<style scoped>
.treemap-wrapper {
    position: relative;
    width: 100%;
}

.treemap-container {
    width: 100%;
    min-height: 500px;
}

.chart-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 12px;
    padding: 8px;
    background: #fafafa;
    border-radius: 4px;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    user-select: none;
    transition: opacity 0.2s;
}

.legend-item:hover {
    opacity: 1 !important;
}

.legend-item .swatch {
    width: 16px;
    height: 16px;
    border-radius: 2px;
    flex-shrink: 0;
}

.legend-item .label {
    font-size: 13px;
    color: #333;
}
</style>
