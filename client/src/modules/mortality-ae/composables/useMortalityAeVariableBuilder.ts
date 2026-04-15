import { computed, nextTick, ref, watch } from 'vue';
import type { Ref } from 'vue';

import type { ApiDatasetSchemaResults } from '@/types/datasets';

import type { ApiAeAtomicVariable } from '../types';

type SchemaColumn = ApiDatasetSchemaResults['columns'][number];

export type NumericBinningMode = 'uniform' | 'quintile' | 'custom';
export type CategoricalGroupCount = 'all' | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

export type CategoricalGroup = {
    name: string;
    values: string[];
    x_position: string;
};

export type CrossGroup = {
    name: string;
    a_any: boolean;
    a_values: string[];
    b_any: boolean;
    b_values: string[];
    x_position: string;
};

export const CROSS_SENTINEL = '__cross__';

export function useMortalityAeVariableBuilder(args: {
    schema: Ref<ApiDatasetSchemaResults | null>;
}) {
    const { schema } = args;

    const xVarName = ref<string | null>(null);
    const xNumericBinning = ref<NumericBinningMode>('quintile');
    const xNumericBinCount = ref<number>(5);
    const xNumericCustomEdgesRaw = ref<string>('');
    const xCatGroupCount = ref<CategoricalGroupCount>('all');
    const xCatGroups = ref<CategoricalGroup[]>([]);
    const xCatRemainingName = ref<string>('Remaining');
    const xCatRemainingPosition = ref<string>('');

    const xCrossAName = ref<string | null>(null);
    const xCrossBName = ref<string | null>(null);
    const xCrossANumericBinning = ref<NumericBinningMode>('quintile');
    const xCrossANumericBinCount = ref<number>(5);
    const xCrossANumericCustomEdgesRaw = ref<string>('');
    const xCrossBNumericBinning = ref<NumericBinningMode>('quintile');
    const xCrossBNumericBinCount = ref<number>(5);
    const xCrossBNumericCustomEdgesRaw = ref<string>('');
    const xCrossGroupCount = ref<CategoricalGroupCount>(2);
    const xCrossGroups = ref<CrossGroup[]>([]);
    const xCrossRemainingName = ref<string>('Remaining');
    const xCrossRemainingPosition = ref<string>('');
    const xCrossALabels = ref<string[] | null>(null);
    const xCrossBLabels = ref<string[] | null>(null);
    const xCrossALabelsLoading = ref(false);
    const xCrossBLabelsLoading = ref(false);
    const xCrossALabelError = ref<string | null>(null);
    const xCrossBLabelError = ref<string | null>(null);

    const splitVarName = ref<string | null>(null);
    const splitNumericBinning = ref<NumericBinningMode>('quintile');
    const splitNumericBinCount = ref<number>(5);
    const splitNumericCustomEdgesRaw = ref<string>('');
    const splitCatGroupCount = ref<CategoricalGroupCount>('all');
    const splitCatGroups = ref<CategoricalGroup[]>([]);
    const splitCatRemainingName = ref<string>('Remaining');
    const splitCatRemainingPosition = ref<string>('');

    const splitCrossAName = ref<string | null>(null);
    const splitCrossBName = ref<string | null>(null);
    const splitCrossANumericBinning = ref<NumericBinningMode>('quintile');
    const splitCrossANumericBinCount = ref<number>(5);
    const splitCrossANumericCustomEdgesRaw = ref<string>('');
    const splitCrossBNumericBinning = ref<NumericBinningMode>('quintile');
    const splitCrossBNumericBinCount = ref<number>(5);
    const splitCrossBNumericCustomEdgesRaw = ref<string>('');
    const splitCrossGroupCount = ref<CategoricalGroupCount>(2);
    const splitCrossGroups = ref<CrossGroup[]>([]);
    const splitCrossRemainingName = ref<string>('Remaining');
    const splitCrossRemainingPosition = ref<string>('');
    const splitCrossALabels = ref<string[] | null>(null);
    const splitCrossBLabels = ref<string[] | null>(null);
    const splitCrossALabelsLoading = ref(false);
    const splitCrossBLabelsLoading = ref(false);
    const splitCrossALabelError = ref<string | null>(null);
    const splitCrossBLabelError = ref<string | null>(null);

    const polyDegreeOptions = [
        { label: '1', value: 1 },
        { label: '2', value: 2 },
        { label: '3', value: 3 },
    ];
    const polyEnabled = ref<boolean>(false);
    const polyDegree = ref<number>(1);
    const polyWeighted = ref<boolean>(true);

    const columnMappingOptions = computed(() => {
        if (!schema.value?.column_suggestions) {
            return {
                policy_number: [],
                face_amount: [],
                mac: [],
                mec: [],
                man: [],
                men: [],
                moc: [],
                cola_m1: [],
            };
        }

        const suggestions = schema.value.column_suggestions;
        return {
            policy_number: suggestions.policy_number_candidates.map((candidate) => ({
                label: candidate,
                value: candidate,
            })),
            face_amount: suggestions.face_amount_candidates.map((candidate) => ({
                label: candidate,
                value: candidate,
            })),
            mac: suggestions.mac_candidates.map((candidate) => ({
                label: candidate,
                value: candidate,
            })),
            mec: suggestions.mec_candidates.map((candidate) => ({
                label: candidate,
                value: candidate,
            })),
            man: suggestions.man_candidates.map((candidate) => ({
                label: candidate,
                value: candidate,
            })),
            men: suggestions.men_candidates.map((candidate) => ({
                label: candidate,
                value: candidate,
            })),
            moc: suggestions.moc_candidates.map((candidate) => ({
                label: candidate,
                value: candidate,
            })),
            cola_m1: suggestions.cola_m1_candidates.map((candidate) => ({
                label: candidate,
                value: candidate,
            })),
        };
    });

    const baseVariableOptions = computed(() => {
        if (!schema.value) return [];

        return schema.value.columns
            .filter(
                (column) =>
                    column.name !== schema.value?.mec_column &&
                    column.name !== schema.value?.mac_column,
            )
            .map((column) => ({
                label: `${column.name} (${column.kind})`,
                value: column.name,
            }));
    });

    const xVariableOptions = computed(() => [
        { label: 'Composite (A x B)', value: CROSS_SENTINEL },
        ...baseVariableOptions.value,
    ]);

    const isXCross = computed(() => xVarName.value === CROSS_SENTINEL);

    const xVarInfo = computed(() => {
        if (!schema.value || !xVarName.value || isXCross.value) return null;
        return schema.value.columns.find((column) => column.name === xVarName.value) ?? null;
    });

    const splitVariableOptions = computed(() => [
        { label: 'None', value: null },
        { label: 'Composite (A x B)', value: CROSS_SENTINEL },
        ...baseVariableOptions.value,
    ]);

    const isSplitCross = computed(() => splitVarName.value === CROSS_SENTINEL);

    const splitVarInfo = computed(() => {
        if (!schema.value || !splitVarName.value || isSplitCross.value) return null;
        return (
            schema.value.columns.find((column) => column.name === splitVarName.value) ?? null
        );
    });

    const xCrossAVarInfo = computed(() => {
        if (!schema.value || !xCrossAName.value) return null;
        return schema.value.columns.find((column) => column.name === xCrossAName.value) ?? null;
    });

    const xCrossBVarInfo = computed(() => {
        if (!schema.value || !xCrossBName.value) return null;
        return schema.value.columns.find((column) => column.name === xCrossBName.value) ?? null;
    });

    const splitCrossAVarInfo = computed(() => {
        if (!schema.value || !splitCrossAName.value) return null;
        return (
            schema.value.columns.find((column) => column.name === splitCrossAName.value) ??
            null
        );
    });

    const splitCrossBVarInfo = computed(() => {
        if (!schema.value || !splitCrossBName.value) return null;
        return (
            schema.value.columns.find((column) => column.name === splitCrossBName.value) ??
            null
        );
    });

    const numericBinningOptions = [
        { label: 'Uniform', value: 'uniform' },
        { label: 'Quintile', value: 'quintile' },
        { label: 'Custom', value: 'custom' },
    ] as const;

    const binCountOptions = Array.from({ length: 19 }, (_, index) => {
        const value = index + 2;
        return { label: String(value), value };
    });

    const crossGroupCountOptions = Array.from({ length: 9 }, (_, index) => {
        const value = index + 2;
        return { label: `${value} groups`, value: value as CategoricalGroupCount };
    });

    const xCrossLabelsLoading = computed(
        () => xCrossALabelsLoading.value || xCrossBLabelsLoading.value,
    );

    const splitCrossLabelsLoading = computed(
        () => splitCrossALabelsLoading.value || splitCrossBLabelsLoading.value,
    );

    const xCatUniqueValues = computed(() => {
        if (!xVarInfo.value || xVarInfo.value.kind !== 'categorical') return null;
        const values = xVarInfo.value.unique_values ?? null;
        return values && values.length ? values : null;
    });

    const xCatUniqueCount = computed(() => {
        if (!xVarInfo.value || xVarInfo.value.kind !== 'categorical') return null;
        const uniqueCount = xVarInfo.value.unique_count;
        return typeof uniqueCount === 'number' && Number.isFinite(uniqueCount)
            ? uniqueCount
            : null;
    });

    const xCatAllUniqueAllowed = computed(() => {
        const uniqueCount = xCatUniqueCount.value;
        if (uniqueCount === null) return true;
        return uniqueCount <= 11;
    });

    const splitCatUniqueValues = computed(() => {
        if (!splitVarInfo.value || splitVarInfo.value.kind !== 'categorical') return null;
        const values = splitVarInfo.value.unique_values ?? null;
        return values && values.length ? values : null;
    });

    const splitCatUniqueCount = computed(() => {
        if (!splitVarInfo.value || splitVarInfo.value.kind !== 'categorical') return null;
        const uniqueCount = splitVarInfo.value.unique_count;
        return typeof uniqueCount === 'number' && Number.isFinite(uniqueCount)
            ? uniqueCount
            : null;
    });

    const splitCatAllUniqueAllowed = computed(() => {
        const uniqueCount = splitCatUniqueCount.value;
        if (uniqueCount === null) return true;
        return uniqueCount <= 11;
    });

    const categoricalGroupCountOptions = computed(() => {
        const uniqueCount = xCatUniqueCount.value;
        const maxGroups = Math.max(0, Math.min(10, uniqueCount ?? 10) + 2);
        const options: Array<{ label: string; value: CategoricalGroupCount }> = [];

        if (xCatAllUniqueAllowed.value) {
            options.push({ label: 'All unique', value: 'all' });
        }

        for (let value = 2; value <= maxGroups; value += 1) {
            options.push({
                label: `${value} groups`,
                value: value as CategoricalGroupCount,
            });
        }

        return options;
    });

    const splitCategoricalGroupCountOptions = computed(() => {
        const uniqueCount = splitCatUniqueCount.value;
        const maxGroups = Math.max(0, Math.min(10, uniqueCount ?? 10) + 2);
        const options: Array<{ label: string; value: CategoricalGroupCount }> = [];

        if (splitCatAllUniqueAllowed.value) {
            options.push({ label: 'All unique', value: 'all' });
        }

        for (let value = 2; value <= maxGroups; value += 1) {
            options.push({
                label: `${value} groups`,
                value: value as CategoricalGroupCount,
            });
        }

        return options;
    });

    const xCatRemainingValues = computed(() => {
        const uniques = xCatUniqueValues.value;
        if (!uniques) return [];
        const chosen = new Set(xCatGroups.value.flatMap((group) => group.values));
        return uniques.filter((value) => !chosen.has(value));
    });

    const xCatRemainingPreview = computed(() => {
        const remaining = xCatRemainingValues.value;
        const preview = remaining.slice(0, 25);
        const suffix =
            remaining.length > preview.length
                ? ` ... (+${remaining.length - preview.length})`
                : '';
        return preview.join(', ') + suffix;
    });

    const splitCatRemainingValues = computed(() => {
        const uniques = splitCatUniqueValues.value;
        if (!uniques) return [];
        const chosen = new Set(splitCatGroups.value.flatMap((group) => group.values));
        return uniques.filter((value) => !chosen.has(value));
    });

    const splitCatRemainingPreview = computed(() => {
        const remaining = splitCatRemainingValues.value;
        const preview = remaining.slice(0, 25);
        const suffix =
            remaining.length > preview.length
                ? ` ... (+${remaining.length - preview.length})`
                : '';
        return preview.join(', ') + suffix;
    });

    function hasTooManyUniquesForUi(info: SchemaColumn | null): boolean {
        if (!info || info.kind !== 'categorical') return false;

        const uniqueCount = info.unique_count;
        const values = info.unique_values;

        if (typeof uniqueCount !== 'number' || !Number.isFinite(uniqueCount)) {
            return false;
        }
        if (!values) {
            return true;
        }
        return values.length < uniqueCount;
    }

    const xCrossTooManyUniques = computed(() => {
        if (!isXCross.value) return false;
        if (hasTooManyUniquesForUi(xCrossAVarInfo.value)) return true;
        if (hasTooManyUniquesForUi(xCrossBVarInfo.value)) return true;

        const errors = `${xCrossALabelError.value || ''} ${xCrossBLabelError.value || ''}`;
        return errors.toLowerCase().includes('too many unique');
    });

    const splitCrossTooManyUniques = computed(() => {
        if (!isSplitCross.value) return false;
        if (hasTooManyUniquesForUi(splitCrossAVarInfo.value)) return true;
        if (hasTooManyUniquesForUi(splitCrossBVarInfo.value)) return true;

        const errors = `${splitCrossALabelError.value || ''} ${splitCrossBLabelError.value || ''}`;
        return errors.toLowerCase().includes('too many unique');
    });

    function parseNumericEdges(raw: string): number[] {
        return (raw || '')
            .split(/[ ,]+/)
            .filter(Boolean)
            .map((segment) => Number(segment))
            .filter((value) => Number.isFinite(value));
    }

    function parseDateEdges(raw: string): string[] {
        return (raw || '')
            .split(/[ ,]+/)
            .map((segment) => segment.trim())
            .filter(Boolean);
    }

    function makeAtomicVariableSpec(args: {
        info: SchemaColumn;
        name: string;
        numericBinning: NumericBinningMode;
        numericBinCount: number;
        numericCustomEdgesRaw: string;
    }): ApiAeAtomicVariable {
        const {
            info,
            name,
            numericBinning,
            numericBinCount,
            numericCustomEdgesRaw,
        } = args;

        if (info.kind === 'numeric') {
            return {
                kind: 'numeric',
                name,
                binning: numericBinning,
                bin_count: numericBinning === 'custom' ? null : numericBinCount,
                custom_edges:
                    numericBinning === 'custom'
                        ? parseNumericEdges(numericCustomEdgesRaw)
                        : null,
            };
        }

        if (info.kind === 'date') {
            return {
                kind: 'date',
                name,
                binning: numericBinning,
                bin_count: numericBinning === 'custom' ? null : numericBinCount,
                custom_edges:
                    numericBinning === 'custom'
                        ? parseDateEdges(numericCustomEdgesRaw)
                        : null,
            };
        }

        return {
            kind: 'categorical',
            name,
            grouping: 'all_unique',
            groups: null,
            remaining_name: 'Remaining',
            remaining_position: null,
        };
    }

    function normalizeCrossGroupCount(value: CategoricalGroupCount): number {
        return typeof value === 'number' && Number.isFinite(value) ? Math.max(2, value) : 2;
    }

    function ensureCrossGroups(count: number, groups: CrossGroup[]): CrossGroup[] {
        const desired = Math.max(2, Math.min(10, count)) - 1;
        const nextGroups = groups.slice(0, desired);

        while (nextGroups.length < desired) {
            nextGroups.push({
                name: `Group ${nextGroups.length + 1}`,
                a_any: false,
                a_values: [],
                b_any: false,
                b_values: [],
                x_position: '',
            });
        }

        return nextGroups;
    }

    const schemaSummary = computed(() => {
        if (!schema.value) return null;

        const numeric = schema.value.columns.filter((column) => column.kind === 'numeric').length;
        const date = schema.value.columns.filter((column) => column.kind === 'date').length;
        const categorical = schema.value.columns.filter(
            (column) => column.kind === 'categorical',
        ).length;

        return {
            total: schema.value.columns.length,
            numeric,
            date,
            categorical,
            mac: schema.value.mac_column,
            mec: schema.value.mec_column,
        };
    });

    function parseOptionalNumber(raw: string): number | null {
        const value = (raw || '').trim();
        if (!value) return null;

        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : null;
    }

    const polyFitEligible = computed(() => {
        if (!xVarName.value) return false;

        if (isXCross.value) {
            const groupPositionsOk = xCrossGroups.value.every(
                (group) => parseOptionalNumber(group.x_position) !== null,
            );
            const remainingOk = parseOptionalNumber(xCrossRemainingPosition.value) !== null;
            return groupPositionsOk && remainingOk;
        }

        if (!xVarInfo.value) return false;
        if (xVarInfo.value.kind === 'numeric') return true;
        if (xVarInfo.value.kind === 'date') return true;
        if (xVarInfo.value.kind !== 'categorical') return false;
        if (xCatGroupCount.value === 'all') return false;

        const groupPositionsOk = xCatGroups.value.every(
            (group) => parseOptionalNumber(group.x_position) !== null,
        );
        const remainingOk = parseOptionalNumber(xCatRemainingPosition.value) !== null;
        return groupPositionsOk && remainingOk;
    });

    function crossGroupIsInvalid(group: CrossGroup): boolean {
        if (group.a_any && group.b_any) return true;
        if (!group.a_any && group.a_values.length === 0) return true;
        if (!group.b_any && group.b_values.length === 0) return true;
        return false;
    }

    function clearCrossState(which: 'x' | 'split') {
        if (which === 'x') {
            xCrossAName.value = null;
            xCrossBName.value = null;
            xCrossGroups.value = [];
            xCrossRemainingName.value = 'Remaining';
            xCrossRemainingPosition.value = '';
            return;
        }

        splitCrossAName.value = null;
        splitCrossBName.value = null;
        splitCrossGroups.value = [];
        splitCrossRemainingName.value = 'Remaining';
        splitCrossRemainingPosition.value = '';
    }

    async function applyAtomicVariableToState(
        which: 'x' | 'split',
        variable: ApiAeAtomicVariable | null,
    ) {
        if (which === 'x') {
            xVarName.value = variable?.name ?? null;
        } else {
            splitVarName.value = variable?.name ?? null;
        }

        clearCrossState(which);
        await nextTick();

        if (variable === null) {
            return;
        }

        if (which === 'x') {
            if (variable.kind === 'numeric' || variable.kind === 'date') {
                xNumericBinning.value = variable.binning;
                xNumericBinCount.value = variable.bin_count ?? 5;
                xNumericCustomEdgesRaw.value = (variable.custom_edges ?? []).join(', ');
                return;
            }

            xCatGroupCount.value =
                variable.grouping === 'custom'
                    ? ((variable.groups?.length ?? 0) + 1 as CategoricalGroupCount)
                    : 'all';
            xCatGroups.value = (variable.groups ?? []).map((group) => ({
                name: group.name,
                values: [...group.values],
                x_position:
                    group.x_position === null || group.x_position === undefined
                        ? ''
                        : String(group.x_position),
            }));
            xCatRemainingName.value = variable.remaining_name ?? 'Remaining';
            xCatRemainingPosition.value =
                variable.remaining_position === null ||
                variable.remaining_position === undefined
                    ? ''
                    : String(variable.remaining_position);
            return;
        }

        if (variable.kind === 'numeric' || variable.kind === 'date') {
            splitNumericBinning.value = variable.binning;
            splitNumericBinCount.value = variable.bin_count ?? 5;
            splitNumericCustomEdgesRaw.value = (variable.custom_edges ?? []).join(', ');
            return;
        }

        splitCatGroupCount.value =
            variable.grouping === 'custom'
                ? ((variable.groups?.length ?? 0) + 1 as CategoricalGroupCount)
                : 'all';
        splitCatGroups.value = (variable.groups ?? []).map((group) => ({
            name: group.name,
            values: [...group.values],
            x_position:
                group.x_position === null || group.x_position === undefined
                    ? ''
                    : String(group.x_position),
        }));
        splitCatRemainingName.value = variable.remaining_name ?? 'Remaining';
        splitCatRemainingPosition.value =
            variable.remaining_position === null ||
            variable.remaining_position === undefined
                ? ''
                : String(variable.remaining_position);
    }

    watch(
        () => xCrossGroupCount.value,
        (next) => {
            xCrossGroups.value = ensureCrossGroups(
                normalizeCrossGroupCount(next),
                xCrossGroups.value,
            );
        },
        { immediate: true },
    );

    watch(
        () => splitCrossGroupCount.value,
        (next) => {
            splitCrossGroups.value = ensureCrossGroups(
                normalizeCrossGroupCount(next),
                splitCrossGroups.value,
            );
        },
        { immediate: true },
    );

    watch(
        () => xVarName.value,
        () => {
            if (!isXCross.value) return;
            const desired = normalizeCrossGroupCount(xCrossGroupCount.value);
            if (xCrossGroups.value.length !== desired - 1) {
                xCrossGroups.value = ensureCrossGroups(desired, xCrossGroups.value);
            }
        },
        { immediate: true },
    );

    watch(
        () => splitVarName.value,
        () => {
            if (!isSplitCross.value) return;
            const desired = normalizeCrossGroupCount(splitCrossGroupCount.value);
            if (splitCrossGroups.value.length !== desired - 1) {
                splitCrossGroups.value = ensureCrossGroups(desired, splitCrossGroups.value);
            }
        },
        { immediate: true },
    );

    watch(
        () => xCatGroupCount.value,
        () => {
            if (xCatGroupCount.value === 'all') {
                xCatGroups.value = [];
                xCatRemainingName.value = 'Remaining';
                xCatRemainingPosition.value = '';
                return;
            }

            const groupsToDefine = Math.max(0, Number(xCatGroupCount.value) - 1);
            const nextGroups: CategoricalGroup[] = [];

            for (let index = 0; index < groupsToDefine; index += 1) {
                nextGroups.push({
                    name: `Group ${index + 1}`,
                    values: [],
                    x_position: '',
                });
            }

            xCatGroups.value = nextGroups;
        },
        { immediate: true },
    );

    watch(
        () => categoricalGroupCountOptions.value,
        (options) => {
            const allowed = new Set(options.map((option) => option.value));
            if (allowed.size === 0) return;
            if (!allowed.has(xCatGroupCount.value)) {
                xCatGroupCount.value = xCatAllUniqueAllowed.value ? 'all' : 2;
            }
        },
        { immediate: true },
    );

    watch(
        () => splitCatGroupCount.value,
        () => {
            if (splitCatGroupCount.value === 'all') {
                splitCatGroups.value = [];
                splitCatRemainingName.value = 'Remaining';
                splitCatRemainingPosition.value = '';
                return;
            }

            const groupsToDefine = Math.max(0, Number(splitCatGroupCount.value) - 1);
            const nextGroups: CategoricalGroup[] = [];

            for (let index = 0; index < groupsToDefine; index += 1) {
                nextGroups.push({
                    name: `Group ${index + 1}`,
                    values: [],
                    x_position: '',
                });
            }

            splitCatGroups.value = nextGroups;
        },
        { immediate: true },
    );

    watch(
        () => splitCategoricalGroupCountOptions.value,
        (options) => {
            const allowed = new Set(options.map((option) => option.value));
            if (allowed.size === 0) return;
            if (!allowed.has(splitCatGroupCount.value)) {
                splitCatGroupCount.value = splitCatAllUniqueAllowed.value ? 'all' : 2;
            }
        },
        { immediate: true },
    );

    watch(
        () => xVarInfo.value?.kind,
        (kind) => {
            if (!kind) return;

            if (kind === 'numeric') {
                xCatGroupCount.value = 'all';
                xCatGroups.value = [];
                xCatRemainingName.value = 'Remaining';
                xCatRemainingPosition.value = '';
                return;
            }

            xNumericBinning.value = 'quintile';
            xNumericBinCount.value = 5;
            xNumericCustomEdgesRaw.value = '';
            xCatGroupCount.value = xCatAllUniqueAllowed.value ? 'all' : 2;
        },
    );

    watch(
        () => xVarName.value,
        () => {
            xNumericBinning.value = 'quintile';
            xNumericBinCount.value = 5;
            xNumericCustomEdgesRaw.value = '';
            xCatGroupCount.value = xCatAllUniqueAllowed.value ? 'all' : 2;
            xCatGroups.value = [];
            xCatRemainingName.value = 'Remaining';
            xCatRemainingPosition.value = '';
        },
    );

    watch(
        () => splitVarInfo.value?.kind,
        (kind) => {
            if (!kind) return;

            if (kind === 'numeric') {
                splitCatGroupCount.value = 'all';
                splitCatGroups.value = [];
                splitCatRemainingName.value = 'Remaining';
                splitCatRemainingPosition.value = '';
                return;
            }

            splitNumericBinning.value = 'quintile';
            splitNumericBinCount.value = 5;
            splitNumericCustomEdgesRaw.value = '';
            splitCatGroupCount.value = splitCatAllUniqueAllowed.value ? 'all' : 2;
        },
    );

    watch(
        () => splitVarName.value,
        () => {
            splitNumericBinning.value = 'quintile';
            splitNumericBinCount.value = 5;
            splitNumericCustomEdgesRaw.value = '';
            splitCatGroupCount.value = splitCatAllUniqueAllowed.value ? 'all' : 2;
            splitCatGroups.value = [];
            splitCatRemainingName.value = 'Remaining';
            splitCatRemainingPosition.value = '';
        },
    );

    const inputBindings = {
        columnMappingOptions,
        baseVariableOptions,
        xVariableOptions,
        isXCross,
        xVarInfo,
        splitVariableOptions,
        isSplitCross,
        splitVarInfo,
        xCrossAVarInfo,
        xCrossBVarInfo,
        splitCrossAVarInfo,
        splitCrossBVarInfo,
        numericBinningOptions,
        binCountOptions,
        crossGroupCountOptions,
        xCrossLabelsLoading,
        splitCrossLabelsLoading,
        categoricalGroupCountOptions,
        splitCategoricalGroupCountOptions,
        xCatUniqueValues,
        xCatRemainingValues,
        xCatRemainingPreview,
        splitCatUniqueValues,
        splitCatRemainingValues,
        splitCatRemainingPreview,
        xCrossTooManyUniques,
        splitCrossTooManyUniques,
        schemaSummary,
        polyFitEligible,
        xVarName,
        xNumericBinning,
        xNumericBinCount,
        xNumericCustomEdgesRaw,
        xCatGroupCount,
        xCatGroups,
        xCatRemainingName,
        xCatRemainingPosition,
        xCrossAName,
        xCrossBName,
        xCrossANumericBinning,
        xCrossANumericBinCount,
        xCrossANumericCustomEdgesRaw,
        xCrossBNumericBinning,
        xCrossBNumericBinCount,
        xCrossBNumericCustomEdgesRaw,
        xCrossGroupCount,
        xCrossGroups,
        xCrossRemainingName,
        xCrossRemainingPosition,
        xCrossALabels,
        xCrossBLabels,
        splitVarName,
        splitNumericBinning,
        splitNumericBinCount,
        splitNumericCustomEdgesRaw,
        splitCatGroupCount,
        splitCatGroups,
        splitCatRemainingName,
        splitCatRemainingPosition,
        splitCrossAName,
        splitCrossBName,
        splitCrossANumericBinning,
        splitCrossANumericBinCount,
        splitCrossANumericCustomEdgesRaw,
        splitCrossBNumericBinning,
        splitCrossBNumericBinCount,
        splitCrossBNumericCustomEdgesRaw,
        splitCrossGroupCount,
        splitCrossGroups,
        splitCrossRemainingName,
        splitCrossRemainingPosition,
        splitCrossALabels,
        splitCrossBLabels,
        polyDegreeOptions,
        polyEnabled,
        polyDegree,
        polyWeighted,
    };

    return {
        inputBindings,
        xVarName,
        xNumericBinning,
        xNumericBinCount,
        xNumericCustomEdgesRaw,
        xCatGroupCount,
        xCatGroups,
        xCatRemainingName,
        xCatRemainingPosition,
        xCrossAName,
        xCrossBName,
        xCrossANumericBinning,
        xCrossANumericBinCount,
        xCrossANumericCustomEdgesRaw,
        xCrossBNumericBinning,
        xCrossBNumericBinCount,
        xCrossBNumericCustomEdgesRaw,
        xCrossGroupCount,
        xCrossGroups,
        xCrossRemainingName,
        xCrossRemainingPosition,
        splitVarName,
        splitNumericBinning,
        splitNumericBinCount,
        splitNumericCustomEdgesRaw,
        splitCatGroupCount,
        splitCatGroups,
        splitCatRemainingName,
        splitCatRemainingPosition,
        splitCrossAName,
        splitCrossBName,
        splitCrossANumericBinning,
        splitCrossANumericBinCount,
        splitCrossANumericCustomEdgesRaw,
        splitCrossBNumericBinning,
        splitCrossBNumericBinCount,
        splitCrossBNumericCustomEdgesRaw,
        splitCrossGroupCount,
        splitCrossGroups,
        splitCrossRemainingName,
        splitCrossRemainingPosition,
        polyEnabled,
        polyDegree,
        polyWeighted,
        xVarInfo,
        splitVarInfo,
        xCrossAVarInfo,
        xCrossBVarInfo,
        splitCrossAVarInfo,
        splitCrossBVarInfo,
        isXCross,
        isSplitCross,
        xCatUniqueValues,
        splitCatUniqueValues,
        xCrossTooManyUniques,
        splitCrossTooManyUniques,
        polyFitEligible,
        makeAtomicVariableSpec,
        parseNumericEdges,
        parseDateEdges,
        parseOptionalNumber,
        normalizeCrossGroupCount,
        crossGroupIsInvalid,
        applyAtomicVariableToState,
    };
}

export type MortalityAeVariableBuilder = ReturnType<
    typeof useMortalityAeVariableBuilder
>;
