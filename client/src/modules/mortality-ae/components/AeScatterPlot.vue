<template>
    <div ref="wrapEl" class="plot-wrap">
        <div ref="plotEl" class="plot"></div>
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
        <div class="chart-controls">
            <q-checkbox
                v-if="showLogToggle"
                v-model="logScale"
                dense
                label="Log Scale"
                :disable="!logAllowed"
            />
        </div>
        <div v-if="tooltip.visible" class="tooltip" :style="tooltipStyle">
            <div class="tooltip-title">{{ tooltip.title }}</div>
            <div v-if="tooltip.splitGroup" class="tooltip-row">
                <span class="k">{{ splitLabel }}</span><span class="v">{{ tooltip.splitGroup }}</span>
            </div>
            <div class="tooltip-row">
                <span class="k">{{ props.metric === 'count' ? 'A/E by Count' : 'A/E by Amount' }}</span><span class="v">{{ tooltip.ae }}</span>
            </div>
            <div class="tooltip-row">
                <span class="k">Policy Count</span><span class="v">{{ tooltip.sampleSize }}</span>
            </div>
            <div class="tooltip-row">
                <span class="k">{{ props.metric === 'count' ? 'Deaths (MAC)' : 'Deaths (MAN)' }}</span><span class="v">{{ tooltip.deaths }}</span>
            </div>
            <div v-if="tooltip.avgX !== null" class="tooltip-row">
                <span class="k">Avg {{ variableName }}</span
                ><span class="v">{{ tooltip.avgX }}</span>
            </div>
            <div v-if="tooltip.expected !== null" class="tooltip-row">
                <span class="k">{{ props.metric === 'count' ? 'Expected (MEC)' : 'Expected (MEN)' }}</span><span class="v">{{ tooltip.expected }}</span>
            </div>
            <div v-if="tooltip.ciLower !== null && tooltip.ciUpper !== null" class="tooltip-row">
                <span class="k">95% CI</span><span class="v">[{{ tooltip.ciLower }}, {{ tooltip.ciUpper }}]</span>
            </div>
        </div>
        <div v-if="!hasPoints" class="empty"></div>
    </div>
</template>

<script setup lang="ts">
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';

import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import type {
    ApiAePolynomialFitResults,
    ApiAeUnivariateRow,
    ApiAeUnivariateSplitResults,
} from '@/modules/mortality-ae/types';
import { formatDateTimeSeconds, formatNumericForVariable } from '@/utils/format';

type XAxisKind = 'numeric' | 'date' | 'categorical';

const props = withDefaults(defineProps<{
    rows: ApiAeUnivariateRow[];
    xAxisKind: XAxisKind;
    variableName: string;
    numericDomain?: { min: number; max: number } | null;
    splitResults?: ApiAeUnivariateSplitResults[] | null;
    splitVariableName?: string | null;
    polyFit?: ApiAePolynomialFitResults | null;
    metric?: 'count' | 'amount';
    showOverall?: boolean;
    splitVisible?: Record<string, boolean>;
}>(), {
    metric: 'count',
    showOverall: true,
    splitVisible: () => ({}),
});

const emit = defineEmits<{
    'update:showOverall': [value: boolean];
    'update:splitVisible': [value: Record<string, boolean>];
}>();

const plotEl = ref<HTMLDivElement | null>(null);
const wrapEl = ref<HTMLDivElement | null>(null);

const hoveredIdx = ref<number | null>(null);
const plot = ref<uPlot | null>(null);
const logScale = ref(false);

function isFiniteNumber(x: unknown): x is number {
    return typeof x === 'number' && Number.isFinite(x);
}

type ChartPoint = {
    splitGroup: string | null;
    row: ApiAeUnivariateRow;
};

const showLogToggle = computed(() => props.xAxisKind === 'numeric');
const logAllowed = computed(() => {
    const dom = props.numericDomain;
    if (!dom) return false;
    return dom.min > 0 && dom.max > 0;
});

const splitLabel = computed(() => {
    const nm = (props.splitVariableName || "").trim();
    return nm || "Split";
});

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

const overallRows = computed(() => {
    return props.rows.filter((r) => r.variable_group !== 'Total');
});

function getAeValue(row: ApiAeUnivariateRow): number | null {
    return props.metric === 'count' ? row.ae : row.ae_amount;
}

function getDeathsValue(row: ApiAeUnivariateRow): number {
    return props.metric === 'count' ? row.deaths : (row.actual_amount ?? 0);
}

function isRowChartable(row: ApiAeUnivariateRow): boolean {
    const aeValue = getAeValue(row);
    if (!isFiniteNumber(aeValue)) return false;
    if (props.xAxisKind === 'numeric' || props.xAxisKind === 'date') {
        if (!isFiniteNumber(row.avg_x)) return false;
        if (props.xAxisKind === 'numeric' && logScale.value && logAllowed.value)
            return (row.avg_x as number) > 0;
        return true;
    }
    return true;
}

const chartPoints = computed(() => {
    const pts: ChartPoint[] = [];

    if (props.showOverall) {
        for (const row of overallRows.value) {
            if (!isRowChartable(row)) continue;
            pts.push({ splitGroup: null, row });
        }
    }

    if (props.splitResults && props.splitResults.length) {
        for (const split of props.splitResults) {
            if (!props.splitVisible[split.split_group]) continue;
            for (const row of split.rows) {
                if (row.variable_group === 'Total') continue;
                if (!isRowChartable(row)) continue;
                pts.push({ splitGroup: split.split_group, row });
            }
        }
    }

    return pts;
});

const hasPoints = computed(() => chartPoints.value.length > 0);

function formatNumber(x: number, maxFrac: number): string {
    return Intl.NumberFormat(undefined, { maximumFractionDigits: maxFrac }).format(x);
}

function computeExpected(deaths: number, ae: number | null): number | null {
    if (ae === null || !Number.isFinite(ae) || ae === 0) return null;
    return deaths / ae;
}

function clampAeForPlot(ae: number): number {
    if (!Number.isFinite(ae)) return ae;
    const maxAe = 2.5;
    return ae > maxAe ? maxAe : ae;
}

function radiusForSample(sampleSize: number, min: number, max: number): number {
    const minR = 8;
    const maxR = 22;
    const a = Math.sqrt(Math.max(0, min));
    const b = Math.sqrt(Math.max(0, max));
    const x = Math.sqrt(Math.max(0, sampleSize));
    if (b === a) return (minR + maxR) / 2;
    const t = (x - a) / (b - a);
    return minR + Math.max(0, Math.min(1, t)) * (maxR - minR);
}

function toRgba(color: string, alpha: number): string {
    const c = (color || '').trim();
    if (!c) return c;
    if (c.startsWith('#')) {
        const hex = c.slice(1);
        if (hex.length === 3) {
            const r = parseInt(hex[0] + hex[0], 16);
            const g = parseInt(hex[1] + hex[1], 16);
            const b = parseInt(hex[2] + hex[2], 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }
        if (hex.length === 6) {
            const r = parseInt(hex.slice(0, 2), 16);
            const g = parseInt(hex.slice(2, 4), 16);
            const b = parseInt(hex.slice(4, 6), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }
        return c;
    }
    const rgbaMatch = c.match(
        /^rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)$/i,
    );
    if (rgbaMatch) {
        const r = rgbaMatch[1];
        const g = rgbaMatch[2];
        const b = rgbaMatch[3];
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    const rgbMatch = c.match(/^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/i);
    if (rgbMatch) {
        const r = rgbMatch[1];
        const g = rgbMatch[2];
        const b = rgbMatch[3];
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    return c;
}

function buildPlotData(): {
    data: uPlot.AlignedData;
    meta: Array<{
        key: string;
        splitGroup: string | null;
        variableGroup: string;
        sampleSize: number;
        deaths: number;
        ae: number;
        avgX: number | null;
        expected: number | null;
        r: number;
        color: string;
        row: ApiAeUnivariateRow;
    }>;
    xTickLabels: string[] | null;
    xTickCoords: number[] | null;
    xScale: { min: number; max: number };
    yScale: { min: number; max: number };
    overallTotalAe: number | null;
    splitTotalAes: Array<{ splitGroup: string; ae: number; color: string }>;
    overallColor: string;
} {
    const points = chartPoints.value;
    const totalRowForSize = props.rows.find((r) => r.variable_group === 'Total');
    const totalN =
        totalRowForSize && isFiniteNumber(totalRowForSize.sample_size)
            ? totalRowForSize.sample_size
            : null;
    const minN = 1;
    const maxN =
        totalN && totalN >= 1
            ? totalN
            : Math.max(1, ...points.map((p) => p.row.sample_size));

    let xs: number[];
    let xTickLabels: string[] | null = null;
    let xTickCoords: number[] | null = null;
    if (props.xAxisKind === 'numeric' || props.xAxisKind === 'date') {
        const raw = points.map((p) => p.row.avg_x as number);
        const useLog =
            props.xAxisKind === 'numeric' &&
            logScale.value &&
            props.numericDomain !== null &&
            props.numericDomain !== undefined &&
            props.numericDomain.min > 0 &&
            props.numericDomain.max > 0;
        xs = useLog ? raw.map((v) => Math.log10(v)) : raw;
    } else {
        const allHaveCoords = points.every((p) => isFiniteNumber(p.row.x_coord));
        const tickSource = props.rows.filter((r) => r.variable_group !== 'Total');
        const tickPairs = tickSource
            .map((r) => ({
                coord: r.x_coord,
                label: r.variable_group,
            }))
            .filter((p) => isFiniteNumber(p.coord));

        if (allHaveCoords && tickPairs.length) {
            const byCoord = new Map<number, string>();
            for (const p of tickPairs) {
                if (!byCoord.has(p.coord as number)) byCoord.set(p.coord as number, p.label);
            }
            const coords = Array.from(byCoord.keys()).sort((a, b) => a - b);
            xTickCoords = coords;
            xTickLabels = coords.map((c) => byCoord.get(c) ?? '');
            xs = points.map((p) => p.row.x_coord as number);
        } else {
            const overallCategories = overallRows.value
                .filter((r) => r.variable_group !== 'Total')
                .map((r) => r.variable_group);

            const baseCategoryOrder = Array.from(new Set(overallCategories));
            const extraCategories: string[] = [];
            for (const p of points) {
                const k = p.row.variable_group;
                if (!baseCategoryOrder.includes(k) && !extraCategories.includes(k)) {
                    extraCategories.push(k);
                }
            }
            const categoryOrder = [...baseCategoryOrder, ...extraCategories];

            const pos = new Map<string, number>();
            categoryOrder.forEach((k, i) => pos.set(k, i));
            xs = points.map((p) => pos.get(p.row.variable_group) ?? 0);
            xTickLabels = categoryOrder;
        }
    }

    const ys = points.map((p) => clampAeForPlot(getAeValue(p.row) as number));
    
    // Position dodging for split groups
    let xsDodged: number[];
    
    // Calculate dodge offset for each point to prevent overlap
    // Use legend order (from splitGroups) instead of alphabetical
    const visibleInPoints = new Set(
        points
            .map((p) => p.splitGroup)
            .filter((g) => g !== null)
    );
    const visibleSplitGroups = splitGroups.value.filter((g) => visibleInPoints.has(g));
    
    const hasOverall = points.some((p) => p.splitGroup === null);
    const totalGroups = (hasOverall ? 1 : 0) + visibleSplitGroups.length;
    
    // Define base offsets with adaptive spacing based on number of splits
    // Overall shifts LEFT, splits fit within an adaptive span
    let overallOffset = -0.25;  // Fixed left shift for overall
    
    // Adaptive span: fewer splits = tighter clustering
    const numSplits = visibleSplitGroups.length;
    let maxSplitSpan;
    if (numSplits <= 2) {
        maxSplitSpan = 0.12;
    } else if (numSplits === 3) {
        maxSplitSpan = 0.20;
    } else {
        maxSplitSpan = 0.27;
    }
    
    // Calculate split increment based on number of splits to fit within adaptive span
    let splitIncrement = maxSplitSpan; // Default for 1 split
    if (visibleSplitGroups.length > 1) {
        // Divide the span by (n-1) to get spacing between n points
        splitIncrement = maxSplitSpan / (visibleSplitGroups.length - 1);
    }
    
    // Scale offsets based on axis type
    if (props.xAxisKind === 'numeric' || props.xAxisKind === 'date') {
        const xMinOriginal = Math.min(...xs);
        const xMaxOriginal = Math.max(...xs);
        const xRange = xMaxOriginal - xMinOriginal;
        // Scale the offsets to be proportional to data range
        if (xRange > 0) {
            const baseSpan = maxSplitSpan; // Use 0.45 as the base
            const scaleFactor = (xRange * baseSpan) / 30; // Scale relative to range
            overallOffset = -0.25 * scaleFactor / baseSpan;
            splitIncrement = splitIncrement * scaleFactor / baseSpan;
        }
    }
    
    // Create offset map with Plotly-style positioning
    const dodgeOffsetMap = new Map<string | null, number>();
    if (totalGroups > 1) {
        if (hasOverall) {
            // Overall shifts LEFT by fixed amount
            dodgeOffsetMap.set(null, overallOffset);
            // Splits start at anchor (0) and increment RIGHT: 0, 0.15, 0.30, ...
            visibleSplitGroups.forEach((g, i) => {
                dodgeOffsetMap.set(g, i * splitIncrement);
            });
        } else {
            // No overall, center splits around 0
            visibleSplitGroups.forEach((g, i) => {
                const offset = (i - (visibleSplitGroups.length - 1) / 2) * splitIncrement;
                dodgeOffsetMap.set(g, offset);
            });
        }
    } else {
        // Only one group, no dodging needed
        dodgeOffsetMap.set(null, 0);
        visibleSplitGroups.forEach((g) => dodgeOffsetMap.set(g, 0));
    }
    
    // Apply dodge offsets to x coordinates
    xsDodged = xs.map((x, i) => {
        const offset = dodgeOffsetMap.get(points[i].splitGroup) ?? 0;
        return x + offset;
    });
    
    const xMin = Math.min(...xsDodged);
    const xMax = Math.max(...xsDodged);

    const xScale =
        props.xAxisKind === 'numeric' || props.xAxisKind === 'date'
            ? props.numericDomain &&
              isFiniteNumber(props.numericDomain.min) &&
              isFiniteNumber(props.numericDomain.max)
                ? props.xAxisKind === 'numeric' &&
                  logScale.value &&
                  props.numericDomain.min > 0 &&
                  props.numericDomain.max > 0
                    ? {
                          min: Math.log10(props.numericDomain.min),
                          max: Math.log10(props.numericDomain.max),
                      }
                    : { min: props.numericDomain.min, max: props.numericDomain.max }
                : { min: xMin, max: xMax }
            : xTickCoords && xTickCoords.length
              ? (() => {
                    const min = Math.min(...xTickCoords);
                    const max = Math.max(...xTickCoords);
                    const span = max - min;
                    const pad = span === 0 ? 1 : Math.max(0.5, span * 0.05);
                    return { min: min - pad, max: max + pad };
                })()
              : { min: -0.5, max: (xTickLabels?.length ?? 1) - 0.5 };

    const yScale = {
        min: -0.1,
        max: 2.0,
    };

    const overallColor = 'rgba(25, 118, 210, 1)';
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
    const splitColorMap = new Map<string, string>();
    for (let i = 0; i < splitGroups.value.length; i++) {
        const g = splitGroups.value[i];
        if (!splitColorMap.has(g)) splitColorMap.set(g, palette[i % palette.length]);
    }

    const meta = points.map((p) => {
        const r = p.row;
        const ae = getAeValue(r) as number;
        const deaths = getDeathsValue(r);
        const expected = computeExpected(deaths, ae);
        const color =
            p.splitGroup === null ? overallColor : splitColorMap.get(p.splitGroup) ?? '#444';
        return {
            key: p.splitGroup ? `${p.splitGroup}::${r.variable_group}` : r.variable_group,
            splitGroup: p.splitGroup,
            variableGroup: r.variable_group,
            sampleSize: r.sample_size,
            deaths,
            ae,
            avgX: isFiniteNumber(r.avg_x) ? r.avg_x : null,
            expected,
            r: radiusForSample(Math.max(1, Math.min(r.sample_size, maxN)), minN, maxN),
            color,
            row: r,
        };
    });

    const totalRow = props.rows.find((r) => r.variable_group === 'Total');
    const overallTotalAe =
        totalRow && isFiniteNumber(getAeValue(totalRow)) ? (getAeValue(totalRow) as number) : null;

    const splitTotalAes: Array<{ splitGroup: string; ae: number; color: string }> = [];
    if (props.splitResults && props.splitResults.length) {
        for (const split of props.splitResults) {
            if (!props.splitVisible[split.split_group]) continue;
            const total = split.rows.find((r) => r.variable_group === 'Total');
            const totalAeValue = total ? getAeValue(total) : null;
            if (!total || !isFiniteNumber(totalAeValue)) continue;
            splitTotalAes.push({
                splitGroup: split.split_group,
                ae: totalAeValue as number,
                color: splitColorMap.get(split.split_group) ?? '#444',
            });
        }
    }

    return {
        data: [xsDodged, ys],
        meta,
        xTickLabels,
        xTickCoords,
        xScale,
        yScale,
        overallTotalAe,
        splitTotalAes,
        overallColor,
    };
}

const tooltip = ref<{
    visible: boolean;
    left: number;
    top: number;
    title: string;
    splitGroup: string | null;
    ae: string;
    sampleSize: string;
    deaths: string;
    avgX: string | null;
    expected: string | null;
    ciLower: string | null;
    ciUpper: string | null;
}>({
    visible: false,
    left: 0,
    top: 0,
    title: '',
    splitGroup: null,
    ae: '',
    sampleSize: '',
    deaths: '',
    avgX: null,
    expected: null,
    ciLower: null,
    ciUpper: null,
});

const tooltipStyle = computed(() => {
    return {
        left: `${tooltip.value.left}px`,
        top: `${tooltip.value.top}px`,
    };
});

function hideTooltip() {
    tooltip.value.visible = false;
}

function showTooltip(u: uPlot, idx: number, meta: ReturnType<typeof buildPlotData>['meta']) {
    const row = meta[idx];
    const wrap = wrapEl.value;
    if (!wrap) return;

    const rect = wrap.getBoundingClientRect();
    const left = (u.cursor.left ?? 0) + 12;
    const top = (u.cursor.top ?? 0) + 12;

    const maxLeft = rect.width - 240;
    const maxTop = rect.height - 140;

    // Format A/E as percentage with 1 decimal
    const formatAePercent = (ae: number): string => {
        return `${(ae * 100).toFixed(1)}%`;
    };

    // Get CI values if available (based on metric)
    const ciLowerValue = props.metric === 'count' ? row.row.ae_ci_lower : row.row.ae_amount_ci_lower;
    const ciUpperValue = props.metric === 'count' ? row.row.ae_ci_upper : row.row.ae_amount_ci_upper;
    
    const ciLower =
        ciLowerValue != null && isFiniteNumber(ciLowerValue)
            ? formatAePercent(ciLowerValue)
            : null;
    const ciUpper =
        ciUpperValue != null && isFiniteNumber(ciUpperValue)
            ? formatAePercent(ciUpperValue)
            : null;

    tooltip.value = {
        visible: true,
        left: Math.max(0, Math.min(maxLeft, left)),
        top: Math.max(0, Math.min(maxTop, top)),
        title: row.variableGroup,
        splitGroup: row.splitGroup,
        ae: formatAePercent(row.ae),
        sampleSize: formatNumber(row.sampleSize, 0),
        deaths: formatNumber(row.deaths, 2),
        avgX:
            row.avgX === null
                ? null
                : props.xAxisKind === 'date'
                  ? formatDateTimeSeconds(row.avgX)
                  : formatNumericForVariable(props.variableName, row.avgX),
        expected: row.expected === null ? null : formatNumber(row.expected, 2),
        ciLower,
        ciUpper,
    };
}

function nearestPointIndex(
    u: uPlot,
    data: uPlot.AlignedData,
    meta: ReturnType<typeof buildPlotData>['meta'],
): number | null {
    const left = u.cursor.left;
    const top = u.cursor.top;
    if (left === null || left === undefined || top === null || top === undefined) return null;

    // Compare everything in plot-area coordinates (uPlot default):
    // - cursor.{left,top} are relative to plot area
    // - valToPos(val, scale) returns plot-area coords (can=false default)
    const mx = left;
    const my = top;

    let bestIdx: number | null = null;
    let bestDist2 = Number.POSITIVE_INFINITY;

    for (let i = 0; i < meta.length; i++) {
        const xVal = data[0][i] as number;
        const yVal = data[1][i] as number;
        const cx = u.valToPos(xVal, 'x');
        const cy = u.valToPos(yVal, 'y');
        
        // Different hit detection for bars vs circles
        if (meta[i].splitGroup === null) {
            // Bar hit detection for overall
            const barWidth = 60;
            const y0 = u.valToPos(0, 'y');
            
            // Check if mouse is within bar bounds
            if (mx >= cx - barWidth / 2 && mx <= cx + barWidth / 2 &&
                my >= cy && my <= y0) {
                // Within bar, calculate distance from center
                const dx = cx - mx;
                const dy = (cy + y0) / 2 - my; // distance from vertical center of bar
                const dist2 = dx * dx + dy * dy;
                if (dist2 < bestDist2) {
                    bestDist2 = dist2;
                    bestIdx = i;
                }
            }
        } else {
            // Circle hit detection (split groups)
            const dx = cx - mx;
            const dy = cy - my;
            const dist2 = dx * dx + dy * dy;

            const r = meta[i].r;
            const threshold = Math.max(22, r + 10);
            if (dist2 > threshold * threshold) continue;
            if (dist2 < bestDist2) {
                bestDist2 = dist2;
                bestIdx = i;
            }
        }
    }

    return bestIdx;
}

function buildPlot() {
    const el = plotEl.value;
    if (!el) return;

    const {
        data,
        meta,
        xTickLabels,
        xTickCoords,
        xScale,
        yScale,
        overallTotalAe,
        splitTotalAes,
        overallColor,
    } = buildPlotData();
    const useLog = props.xAxisKind === 'numeric' && logScale.value && logAllowed.value;

    const wrap = wrapEl.value;
    const w = wrap ? Math.max(520, wrap.clientWidth) : 920;
    const h = 340;

    function logSplits(min: number, max: number): number[] {
        const start = Math.floor(min);
        const end = Math.ceil(max);
        const splits: number[] = [];
        for (let e = start; e <= end; e++) {
            for (let d = 1; d <= 9; d++) {
                splits.push(e + Math.log10(d));
            }
        }
        const within = splits.filter((v) => v >= min && v <= max);
        within.sort((a, b) => a - b);
        const unique: number[] = [];
        for (const v of within) {
            if (!unique.length || Math.abs(v - unique[unique.length - 1]) > 1e-9) {
                unique.push(v);
            }
        }
        return unique.length ? unique : [min, max];
    }

    const pointsPlugin: uPlot.Plugin = {
        hooks: {
            ready: [
                (u) => {
                    const over = u.over;
                    if (!over) return;
                    const handler = (e: MouseEvent) => {
                        e.preventDefault();
                        e.stopPropagation();
                    };
                    over.addEventListener('dblclick', handler, { passive: false });
                    (u as unknown as { __dblclickHandler?: (e: MouseEvent) => void }).__dblclickHandler =
                        handler;
                },
            ],
            destroy: [
                (u) => {
                    const over = u.over;
                    const h = (u as unknown as { __dblclickHandler?: (e: MouseEvent) => void })
                        .__dblclickHandler;
                    if (over && h) {
                        over.removeEventListener('dblclick', h);
                    }
                },
            ],
            draw: [
                (u) => {
                    const ctx = u.ctx;
                    const idx = hoveredIdx.value;

                    ctx.save();
                    ctx.beginPath();
                    ctx.rect(u.bbox.left, u.bbox.top, u.bbox.width, u.bbox.height);
                    ctx.clip();

                    // Reference lines
                    // A/E = 1 baseline (red dashed)
                    {
                        const y1 = u.valToPos(1, 'y', true);
                        ctx.beginPath();
                        ctx.setLineDash([6, 6]);
                        ctx.moveTo(u.bbox.left, y1);
                        ctx.lineTo(u.bbox.left + u.bbox.width, y1);
                        ctx.strokeStyle = 'rgba(220, 38, 38, 0.8)'; // red
                        ctx.lineWidth = 2;
                        ctx.stroke();
                    }

                    // Best-fit lines (shown only when the series is shown)
                    {
                        const useLog =
                            props.xAxisKind === 'numeric' && logScale.value && logAllowed.value;

                    }

                    // Error bars (draw before points so points appear on top)
                    ctx.setLineDash([]);
                    for (let i = 0; i < meta.length; i++) {
                        const m = meta[i];
                        const row = m.row;
                        
                        // Get CI values based on metric
                        const ciLower = props.metric === 'count' ? row.ae_ci_lower : row.ae_amount_ci_lower;
                        const ciUpper = props.metric === 'count' ? row.ae_ci_upper : row.ae_amount_ci_upper;
                        
                        // Skip CI if A/E is 0
                        if (m.ae === 0) continue;
                        
                        // Check if CI values exist and are valid
                        if (
                            ciLower != null &&
                            ciUpper != null &&
                            isFiniteNumber(ciLower) &&
                            isFiniteNumber(ciUpper)
                        ) {
                            const xVal = data[0][i] as number;
                            const cx = u.valToPos(xVal, 'x', true);
                            
                            const yLower = clampAeForPlot(ciLower);
                            const yUpper = clampAeForPlot(ciUpper);
                            const cyLower = u.valToPos(yLower, 'y', true);
                            const cyUpper = u.valToPos(yUpper, 'y', true);

                            // Use dark slate for overall, regular color for splits
                            const errorBarColor = m.splitGroup === null 
                                ? 'rgba(47, 79, 79, 0.9)' // dark slate for overall
                                : toRgba(m.color, 0.75);

                            // Draw vertical line
                            ctx.beginPath();
                            ctx.moveTo(cx, cyLower);
                            ctx.lineTo(cx, cyUpper);
                            ctx.strokeStyle = errorBarColor;
                            ctx.lineWidth = 2;
                            ctx.stroke();

                            // Draw caps (skip upper cap if CI exceeds y-axis limit)
                            const maxAe = 2.5;
                            const upperClamped = ciUpper > maxAe;
                            const capWidth = 12;
                            ctx.beginPath();
                            // Always draw lower cap
                            ctx.moveTo(cx - capWidth, cyLower);
                            ctx.lineTo(cx + capWidth, cyLower);
                            // Only draw upper cap if not clamped
                            if (!upperClamped) {
                                ctx.moveTo(cx - capWidth, cyUpper);
                                ctx.lineTo(cx + capWidth, cyUpper);
                            }
                            ctx.strokeStyle = errorBarColor;
                            ctx.lineWidth = 2;
                            ctx.stroke();
                        }
                    }

                    // Draw points/bars
                    for (let i = 0; i < meta.length; i++) {
                        const xVal = data[0][i] as number;
                        const yVal = data[1][i] as number;
                        const cx = u.valToPos(xVal, 'x', true);
                        const cy = u.valToPos(yVal, 'y', true);

                        const m = meta[i];
                        
                        // Draw bars for overall, circles for split groups
                        if (m.splitGroup === null) {
                            // Overall group - draw as bar
                            const y0 = u.valToPos(0, 'y', true);
                            const barWidth = 60; // pixels
                            
                            ctx.beginPath();
                            ctx.rect(cx - barWidth / 2, cy, barWidth, y0 - cy);
                            ctx.fillStyle = toRgba(overallColor, 0.7); // match legend color
                            ctx.fill();
                            ctx.lineWidth = i === idx ? 3 : 2;
                            ctx.strokeStyle = i === idx 
                                ? 'rgba(255, 152, 0, 1)' 
                                : overallColor; // match legend color
                            ctx.stroke();
                        } else {
                            // Split groups - draw as circles
                            const r = m.r;
                            ctx.beginPath();
                            ctx.arc(cx, cy, r, 0, Math.PI * 2);
                            ctx.fillStyle = toRgba(m.color, 0.7);
                            ctx.fill();
                            ctx.lineWidth = i === idx ? 2 : 1;
                            ctx.strokeStyle = i === idx ? 'rgba(255, 152, 0, 1)' : m.color;
                            ctx.stroke();
                        }
                    }
                    ctx.restore();
                },
            ],
            setCursor: [
                (u) => {
                    const idx = nearestPointIndex(u, data, meta);
                    if (idx === null) {
                        hoveredIdx.value = null;
                        hideTooltip();
                        return;
                    }
                    hoveredIdx.value = idx;
                    showTooltip(u, idx, meta);
                },
            ],
        },
    };

    const opts: uPlot.Options = {
        width: w,
        height: h * 2,
        scales: {
            x: { min: xScale.min, max: xScale.max, time: false },
            y: { min: yScale.min, max: yScale.max },
        },
        axes: [
            {
                scale: 'x',
                label:
                    props.xAxisKind === 'numeric' && useLog
                        ? `${props.variableName} (log)`
                        : props.variableName,
                stroke: '#000',
                ticks: { stroke: '#000', width: 1 },
                grid: { show: false },
                splits:
                    props.xAxisKind === 'categorical' && xTickLabels
                        ? () =>
                              xTickCoords && xTickCoords.length
                                  ? xTickCoords
                                  : xTickLabels.map((_k, i) => i)
                        : useLog
                          ? (u) => logSplits(u.scales.x.min!, u.scales.x.max!)
                        : undefined,
                values:
                    props.xAxisKind === 'categorical' && xTickLabels
                        ? (_u, ticks) => {
                              if (xTickCoords && xTickCoords.length) {
                                  const byCoord = new Map<number, string>();
                                  for (let i = 0; i < xTickCoords.length; i++) {
                                      byCoord.set(xTickCoords[i], xTickLabels[i] ?? '');
                                  }
                                  const eps = 1e-9;
                                  return ticks.map((t) => {
                                      const direct = byCoord.get(t);
                                      if (direct !== undefined) return direct;
                                      for (const c of xTickCoords) {
                                          if (Math.abs(c - t) <= eps) {
                                              return byCoord.get(c) ?? '';
                                          }
                                      }
                                      return '';
                                  });
                              }
                              return ticks.map((t) => xTickLabels[Math.round(t)] ?? '');
                          }
                        : props.xAxisKind === 'date'
                          ? (_u, ticks) => ticks.map((t) => formatDateTimeSeconds(t))
                          : useLog
                          ? (_u, ticks) => {
                                return ticks.map((t) => {
                                    const decade = Math.floor(t + 1e-12);
                                    const frac = t - decade;
                                    const digit = Math.round(Math.pow(10, frac));
                                    if (![1, 2, 5].includes(digit)) return '';
                                    const value = digit * Math.pow(10, decade);
                                    return formatNumericForVariable(props.variableName, value);
                                });
                            }
                          : undefined,
            },
            {
                scale: 'y',
                label: 'A/E',
                stroke: '#000',
                ticks: { stroke: '#000', width: 1 },
                grid: { show: true, stroke: 'rgba(0,0,0,0.10)', width: 1 },
                splits: () => [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5],
                values: (_u, ticks) => ticks.map((t) => `${(t * 100).toFixed(0)}%`),
            },
        ],
        series: [
            {},
            {
                label: 'A/E',
                stroke: 'rgba(0,0,0,0)',
                width: 0,
                points: { show: false },
            },
        ],
        cursor: {
            y: true,
            drag: { x: false, y: false },
        },
        legend: {
            show: false,
        },
        plugins: [pointsPlugin],
    };

    plot.value = new uPlot(opts, data, el);
}

function destroyPlot() {
    if (plot.value) {
        plot.value.destroy();
        plot.value = null;
    }
    hoveredIdx.value = null;
    hideTooltip();
}

onMounted(() => {
    if (!logAllowed.value) {
        logScale.value = false;
    }
    buildPlot();
});

onBeforeUnmount(() => {
    destroyPlot();
});

watch(
    () => [
        props.rows,
        props.splitResults,
        props.xAxisKind,
        props.variableName,
        props.numericDomain,
        logScale.value,
        props.showOverall,
        props.splitVisible,
    ],
    () => {
        destroyPlot();
        buildPlot();
    },
    { deep: true },
);

watch(
    () => logAllowed.value,
    (allowed) => {
        if (!allowed) logScale.value = false;
    },
    { immediate: true },
);

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
    const prefix = splitName ? `${splitName} ` : '';
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
        emit('update:showOverall', !props.showOverall);
        return;
    }
    if (!key.startsWith('split:')) return;
    const group = key.slice('split:'.length);
    ensureSplitVisibility();
    emit('update:splitVisible', { ...props.splitVisible, [group]: !props.splitVisible[group] });
}

watch(
    () => props.splitResults,
    () => {
        ensureSplitVisibility();
    },
    { immediate: true, deep: true },
);
</script>

<style scoped>
.plot-wrap {
    position: relative;
    width: 100%;
}
.chart-legend {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: 10px 14px;
    padding-top: 10px;
}
.legend-item {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    cursor: pointer;
    user-select: none;
}
.swatch {
    width: 12px;
    height: 12px;
    border-radius: 3px;
    border: 1px solid rgba(0, 0, 0, 0.25);
}
.chart-controls {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding-top: 6px;
    min-height: 30px;
}
.plot {
    width: 100%;
    overflow-x: auto;
    min-height: 680px;
    touch-action: pan-y;
}
.tooltip {
    position: absolute;
    min-width: 220px;
    max-width: 280px;
    padding: 10px 12px;
    border: 1px solid rgba(0, 0, 0, 0.2);
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.98);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
    pointer-events: none;
    font-size: 13px;
    line-height: 1.25;
}
.tooltip-title {
    font-weight: 600;
    margin-bottom: 6px;
}
.tooltip-row {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    margin: 2px 0;
}
.k {
    color: rgba(0, 0, 0, 0.65);
}
.v {
    font-variant-numeric: tabular-nums;
}
.empty {
    padding: 8px 0;
    font-size: 13px;
}
</style>
