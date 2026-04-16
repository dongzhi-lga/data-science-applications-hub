import { computed, nextTick, onMounted, ref, watch } from 'vue';
import type { RouteLocationNormalizedLoaded } from 'vue-router';

import type { ApiDatasetSchemaResults } from '@/types/datasets';
import {
    isMortalityDatasetConfig,
    type ApiDatasetConfig,
} from '@/types/dataset-config';
import {
    getDatasetConfig,
    getDatasetConfigSchema,
    getDatasetConfigs,
} from '@/utils/api';

import {
    getAeInsightsFromConfig,
    postAeUnivariateFromConfig,
    postAeUnivariateFromCsv,
    postAeUploadSchema,
} from '../api';
import type {
    ApiAeInsightDrill,
    ApiAeUnivariateFromConfigParameters,
    ApiAeUnivariateResults,
    ApiAeXVariable,
    ApiAeInsightsResults,
} from '../types';
import type { MortalityAeVariableBuilder } from './useMortalityAeVariableBuilder';

export function useMortalityAeAnalysisState(args: {
    route: RouteLocationNormalizedLoaded;
    getVariables: () => MortalityAeVariableBuilder | null;
}) {
    const { route, getVariables } = args;

    const uploadedFile = ref<File | null>(null);
    const schemaLoading = ref(false);
    const schema = ref<ApiDatasetSchemaResults | null>(null);
    const insightsLoading = ref(false);
    const insightsError = ref<string | null>(null);
    const insightResults = ref<ApiAeInsightsResults | null>(null);

    const configs = ref<ApiDatasetConfig[]>([]);
    const configsLoading = ref(false);
    const selectedConfigId = ref<string | null>(null);

    const selectedConfig = computed(() => {
        if (!selectedConfigId.value) return null;
        return configs.value.find((config) => config.id === selectedConfigId.value) ?? null;
    });

    const configOptions = computed(() =>
        configs.value.map((config) => ({
            label: `${config.dataset_name} (${config.file_path})`,
            value: config.id,
        })),
    );

    const hasDatasetSource = computed(
        () => Boolean(selectedConfigId.value || uploadedFile.value),
    );

    const scatterShowOverall = ref(true);
    const scatterSplitVisible = ref<Record<string, boolean>>({});
    const treemapStateByTab = ref<
        Record<string, { showOverall: boolean; splitVisible: Record<string, boolean> }>
    >({});

    const policyNumberColumn = ref<string | null>(null);
    const faceAmountColumn = ref<string | null>(null);
    const macColumn = ref<string | null>(null);
    const mecColumn = ref<string | null>(null);
    const manColumn = ref<string | null>(null);
    const menColumn = ref<string | null>(null);
    const mocColumn = ref<string | null>(null);
    const colaM1Column = ref<string | null>(null);

    const loading = ref(false);
    const errorMsg = ref<string | null>(null);
    const aeResults = ref<ApiAeUnivariateResults | null>(null);
    const resultsVariableName = ref<string | null>(null);
    const resultsSplitVariableName = ref<string | null>(null);
    const resultsSplitXAxisKind = ref<'numeric' | 'date' | 'categorical' | null>(
        null,
    );
    const resultsXAxisKind = ref<'numeric' | 'date' | 'categorical'>('categorical');
    const resultsXDomain = ref<{ min: number; max: number } | null>(null);
    const resultsTab = ref<string>('overall');
    const colaResultsTab = ref<string>('overall');

    const currentTreemapShowOverall = computed({
        get: () => treemapStateByTab.value[resultsTab.value]?.showOverall ?? true,
        set: (value) => {
            if (!treemapStateByTab.value[resultsTab.value]) {
                treemapStateByTab.value[resultsTab.value] = {
                    showOverall: true,
                    splitVisible: {},
                };
            }
            treemapStateByTab.value[resultsTab.value].showOverall = value;
        },
    });

    const currentTreemapSplitVisible = computed({
        get: () => treemapStateByTab.value[resultsTab.value]?.splitVisible ?? {},
        set: (value) => {
            if (!treemapStateByTab.value[resultsTab.value]) {
                treemapStateByTab.value[resultsTab.value] = {
                    showOverall: true,
                    splitVisible: {},
                };
            }
            treemapStateByTab.value[resultsTab.value].splitVisible = value;
        },
    });

    const canAnalyze = computed(() => {
        const variables = getVariables();
        if (!variables) return false;
        if (!hasDatasetSource.value) return false;
        if (!variables.xVarName.value) return false;
        if (loading.value) return false;

        if (variables.isXCross.value) {
            if (!variables.xCrossAName.value || !variables.xCrossBName.value) return false;
            if (variables.xCrossAName.value === variables.xCrossBName.value) return false;
            if (variables.xCrossTooManyUniques.value) return false;
            const count = variables.normalizeCrossGroupCount(
                variables.xCrossGroupCount.value,
            );
            if (variables.xCrossGroups.value.length !== count - 1) return false;
            if (variables.xCrossGroups.value.some(variables.crossGroupIsInvalid)) {
                return false;
            }
            return true;
        }

        if (!variables.xVarInfo.value) return false;

        if (
            (variables.xVarInfo.value.kind === 'numeric' ||
                variables.xVarInfo.value.kind === 'date') &&
            variables.xNumericBinning.value === 'custom'
        ) {
            const edgesOk =
                variables.xVarInfo.value.kind === 'date'
                    ? variables.parseDateEdges(
                          variables.xNumericCustomEdgesRaw.value,
                      ).length > 0
                    : variables.parseNumericEdges(
                          variables.xNumericCustomEdgesRaw.value,
                      ).length > 0;
            if (!edgesOk) return false;
        }

        if (
            variables.xVarInfo.value.kind === 'categorical' &&
            variables.xCatGroupCount.value !== 'all' &&
            !variables.xCatUniqueValues.value
        ) {
            return false;
        }

        if (variables.isSplitCross.value) {
            if (!variables.splitCrossAName.value || !variables.splitCrossBName.value) {
                return false;
            }
            if (
                variables.splitCrossAName.value === variables.splitCrossBName.value
            ) {
                return false;
            }
            if (variables.splitCrossTooManyUniques.value) return false;
            const count = variables.normalizeCrossGroupCount(
                variables.splitCrossGroupCount.value,
            );
            if (variables.splitCrossGroups.value.length !== count - 1) return false;
            if (variables.splitCrossGroups.value.some(variables.crossGroupIsInvalid)) {
                return false;
            }
        } else if (variables.splitVarName.value) {
            if (!variables.splitVarInfo.value) return false;

            if (
                (variables.splitVarInfo.value.kind === 'numeric' ||
                    variables.splitVarInfo.value.kind === 'date') &&
                variables.splitNumericBinning.value === 'custom'
            ) {
                const edgesOk =
                    variables.splitVarInfo.value.kind === 'date'
                        ? variables.parseDateEdges(
                              variables.splitNumericCustomEdgesRaw.value,
                          ).length > 0
                        : variables.parseNumericEdges(
                              variables.splitNumericCustomEdgesRaw.value,
                          ).length > 0;
                if (!edgesOk) return false;
            }

            if (
                variables.splitVarInfo.value.kind === 'categorical' &&
                variables.splitCatGroupCount.value !== 'all' &&
                !variables.splitCatUniqueValues.value
            ) {
                return false;
            }
        }

        return true;
    });

    async function loadInsightsForConfig(configId: string) {
        insightsLoading.value = true;
        insightsError.value = null;
        insightResults.value = null;

        try {
            insightResults.value = await getAeInsightsFromConfig(configId);
        } catch (error) {
            insightsError.value =
                error instanceof Error ? error.message : 'Failed to load insights';
        } finally {
            insightsLoading.value = false;
        }
    }

    async function onAnalyze() {
        const variables = getVariables();
        if (!variables || !hasDatasetSource.value || !variables.xVarName.value) return;

        loading.value = true;
        errorMsg.value = null;

        try {
            const makeSingleVariableSpec = (which: 'x' | 'split'): ApiAeXVariable => {
                const info =
                    which === 'x' ? variables.xVarInfo.value : variables.splitVarInfo.value;
                const name =
                    which === 'x' ? variables.xVarName.value : variables.splitVarName.value;

                if (!info || !name) {
                    throw new Error('Variable is missing');
                }

                if (info.kind === 'numeric') {
                    const binning =
                        which === 'x'
                            ? variables.xNumericBinning.value
                            : variables.splitNumericBinning.value;
                    const binCount =
                        which === 'x'
                            ? variables.xNumericBinCount.value
                            : variables.splitNumericBinCount.value;
                    const edgesRaw =
                        which === 'x'
                            ? variables.xNumericCustomEdgesRaw.value
                            : variables.splitNumericCustomEdgesRaw.value;

                    return {
                        kind: 'numeric',
                        name,
                        binning,
                        bin_count: binning === 'custom' ? null : binCount,
                        custom_edges:
                            binning === 'custom'
                                ? variables.parseNumericEdges(edgesRaw)
                                : null,
                    };
                }

                if (info.kind === 'date') {
                    const binning =
                        which === 'x'
                            ? variables.xNumericBinning.value
                            : variables.splitNumericBinning.value;
                    const binCount =
                        which === 'x'
                            ? variables.xNumericBinCount.value
                            : variables.splitNumericBinCount.value;
                    const edgesRaw =
                        which === 'x'
                            ? variables.xNumericCustomEdgesRaw.value
                            : variables.splitNumericCustomEdgesRaw.value;

                    return {
                        kind: 'date',
                        name,
                        binning,
                        bin_count: binning === 'custom' ? null : binCount,
                        custom_edges:
                            binning === 'custom'
                                ? variables.parseDateEdges(edgesRaw)
                                : null,
                    };
                }

                const groupCount =
                    which === 'x'
                        ? variables.xCatGroupCount.value
                        : variables.splitCatGroupCount.value;
                const grouping = groupCount === 'all' ? 'all_unique' : 'custom';
                const groups =
                    which === 'x'
                        ? variables.xCatGroups.value
                        : variables.splitCatGroups.value;
                const remainingName =
                    which === 'x'
                        ? variables.xCatRemainingName.value
                        : variables.splitCatRemainingName.value;
                const remainingPosition =
                    which === 'x'
                        ? variables.xCatRemainingPosition.value
                        : variables.splitCatRemainingPosition.value;

                return {
                    kind: 'categorical',
                    name,
                    grouping,
                    groups:
                        grouping === 'custom'
                            ? groups.map((group) => ({
                                  name: group.name,
                                  values: group.values,
                                  x_position: variables.parseOptionalNumber(
                                      group.x_position,
                                  ),
                              }))
                            : null,
                    remaining_name: remainingName,
                    remaining_position:
                        variables.parseOptionalNumber(remainingPosition),
                };
            };

            const makeCrossVariableSpec = (which: 'x' | 'split'): ApiAeXVariable => {
                const isX = which === 'x';
                const aName = isX
                    ? variables.xCrossAName.value
                    : variables.splitCrossAName.value;
                const bName = isX
                    ? variables.xCrossBName.value
                    : variables.splitCrossBName.value;
                const aInfo = isX
                    ? variables.xCrossAVarInfo.value
                    : variables.splitCrossAVarInfo.value;
                const bInfo = isX
                    ? variables.xCrossBVarInfo.value
                    : variables.splitCrossBVarInfo.value;

                if (!aName || !bName || !aInfo || !bInfo) {
                    throw new Error('Composite variables are missing');
                }
                if (aName === bName) {
                    throw new Error('Composite variables must be different');
                }

                const aVar = variables.makeAtomicVariableSpec({
                    info: aInfo,
                    name: aName,
                    numericBinning: isX
                        ? variables.xCrossANumericBinning.value
                        : variables.splitCrossANumericBinning.value,
                    numericBinCount: isX
                        ? variables.xCrossANumericBinCount.value
                        : variables.splitCrossANumericBinCount.value,
                    numericCustomEdgesRaw: isX
                        ? variables.xCrossANumericCustomEdgesRaw.value
                        : variables.splitCrossANumericCustomEdgesRaw.value,
                });

                const bVar = variables.makeAtomicVariableSpec({
                    info: bInfo,
                    name: bName,
                    numericBinning: isX
                        ? variables.xCrossBNumericBinning.value
                        : variables.splitCrossBNumericBinning.value,
                    numericBinCount: isX
                        ? variables.xCrossBNumericBinCount.value
                        : variables.splitCrossBNumericBinCount.value,
                    numericCustomEdgesRaw: isX
                        ? variables.xCrossBNumericCustomEdgesRaw.value
                        : variables.splitCrossBNumericCustomEdgesRaw.value,
                });

                const groups = isX
                    ? variables.xCrossGroups.value
                    : variables.splitCrossGroups.value;
                const remainingName = isX
                    ? variables.xCrossRemainingName.value
                    : variables.splitCrossRemainingName.value;
                const remainingPosition = isX
                    ? variables.xCrossRemainingPosition.value
                    : variables.splitCrossRemainingPosition.value;

                return {
                    kind: 'cross',
                    a_variable: aVar,
                    b_variable: bVar,
                    groups: groups.map((group) => ({
                        name: group.name,
                        a_any: group.a_any,
                        a_values: group.a_values,
                        b_any: group.b_any,
                        b_values: group.b_values,
                        x_position: variables.parseOptionalNumber(group.x_position),
                    })),
                    remaining_name: remainingName,
                    remaining_position:
                        variables.parseOptionalNumber(remainingPosition),
                };
            };

            const xVariable: ApiAeXVariable = variables.isXCross.value
                ? makeCrossVariableSpec('x')
                : makeSingleVariableSpec('x');

            const nextResultsVariableName = variables.isXCross.value
                ? `${variables.xCrossAName.value || 'A'} x ${variables.xCrossBName.value || 'B'}`
                : variables.xVarName.value;

            const splitVariable: ApiAeXVariable | null = variables.splitVarName.value
                ? variables.isSplitCross.value
                    ? makeCrossVariableSpec('split')
                    : variables.splitVarInfo.value
                      ? makeSingleVariableSpec('split')
                      : null
                : null;

            const nextResultsSplitVariableName = variables.splitVarName.value
                ? variables.isSplitCross.value
                    ? `${variables.splitCrossAName.value || 'A'} x ${variables.splitCrossBName.value || 'B'}`
                    : variables.splitVarName.value
                : null;

            const nextResultsSplitXAxisKind = variables.splitVarName.value
                ? 'categorical'
                : null;
            const nextResultsXAxisKind = 'categorical' as const;
            const nextResultsXDomain = null;

            const request = {
                x_variable: xVariable,
                split_variable: splitVariable,
                poly_fit:
                    variables.polyFitEligible.value && variables.polyEnabled.value
                        ? {
                              degree: variables.polyDegree.value as 1 | 2 | 3,
                              weighted: variables.polyWeighted.value,
                          }
                        : null,
            };

            let nextResults: ApiAeUnivariateResults | null = null;

            if (selectedConfigId.value) {
                const params: ApiAeUnivariateFromConfigParameters = {
                    config_id: selectedConfigId.value,
                    ...request,
                };
                nextResults = await postAeUnivariateFromConfig(params);
            } else if (uploadedFile.value) {
                nextResults = await postAeUnivariateFromCsv(uploadedFile.value, {
                    dataset_name: '',
                    ...request,
                    column_mapping: {
                        policy_number_column: policyNumberColumn.value,
                        face_amount_column: faceAmountColumn.value,
                        mac_column: macColumn.value,
                        mec_column: mecColumn.value,
                        man_column: manColumn.value,
                        men_column: menColumn.value,
                        moc_column: mocColumn.value,
                        cola_m1_column: colaM1Column.value,
                    },
                });
            }

            if (!nextResults) {
                throw new Error('Analysis did not return results');
            }

            aeResults.value = nextResults;
            resultsVariableName.value = nextResultsVariableName;
            resultsSplitVariableName.value = nextResultsSplitVariableName;
            resultsSplitXAxisKind.value = nextResultsSplitXAxisKind;
            resultsXAxisKind.value = nextResultsXAxisKind;
            resultsXDomain.value = nextResultsXDomain;
            resultsTab.value = 'overall';
            colaResultsTab.value = 'overall';
        } catch (error) {
            errorMsg.value = error instanceof Error ? error.message : String(error);
        } finally {
            loading.value = false;
        }
    }

    async function applyInsightDrill(drill: ApiAeInsightDrill) {
        const variables = getVariables();
        if (!variables) return;

        await variables.applyAtomicVariableToState('x', drill.x_variable);
        await variables.applyAtomicVariableToState(
            'split',
            drill.split_variable ?? null,
        );
        errorMsg.value = null;
        await nextTick();
        await onAnalyze();
    }

    function splitTabLabel(group: string): string {
        const variableName = (resultsSplitVariableName.value || '').trim();

        if (resultsSplitXAxisKind.value === 'categorical') {
            return group;
        }

        return variableName ? `${variableName} ${group}` : group;
    }

    function formatPolynomialEquation(polyFit: {
        degree: number;
        coefficients: number[];
        weighted: boolean;
    }): string {
        const coefficients = polyFit.coefficients;
        if (!coefficients || coefficients.length === 0) return '';

        const formatCoeff = (value: number): string => value.toFixed(4);
        const terms: string[] = [];
        const degree = coefficients.length - 1;

        for (let index = 0; index <= degree; index += 1) {
            const power = degree - index;
            const coefficient = coefficients[index];

            if (Math.abs(coefficient) < 1e-10) continue;

            const sign = coefficient >= 0 ? '+' : '-';
            const absCoeff = Math.abs(coefficient);

            if (power === 0) {
                terms.push(`${sign} ${formatCoeff(absCoeff)}`);
            } else if (power === 1) {
                terms.push(`${sign} ${formatCoeff(absCoeff)}x`);
            } else if (power === 2) {
                terms.push(`${sign} ${formatCoeff(absCoeff)}x²`);
            } else if (power === 3) {
                terms.push(`${sign} ${formatCoeff(absCoeff)}x³`);
            }
        }

        if (terms.length === 0) {
            return 'y = 0';
        }

        return `y = ${terms.join(' ')}`
            .replace('y = +', 'y = ')
            .replace('y = -', 'y = -');
    }

    async function onLoadUploadedSchema() {
        if (!selectedConfigId.value && !uploadedFile.value) return;

        schemaLoading.value = true;
        errorMsg.value = null;
        schema.value = null;

        if (!selectedConfigId.value) {
            policyNumberColumn.value = null;
            faceAmountColumn.value = null;
            macColumn.value = null;
            mecColumn.value = null;
            manColumn.value = null;
            menColumn.value = null;
            mocColumn.value = null;
            colaM1Column.value = null;
        }

        try {
            if (selectedConfigId.value) {
                schema.value = await getDatasetConfigSchema(selectedConfigId.value);
            } else if (uploadedFile.value) {
                schema.value = await postAeUploadSchema(uploadedFile.value);
            }

            const schemaValue = schema.value;
            if (!selectedConfigId.value && schemaValue?.column_suggestions) {
                const suggestions = schemaValue.column_suggestions;
                policyNumberColumn.value =
                    suggestions.policy_number_candidates[0] || null;
                faceAmountColumn.value =
                    suggestions.face_amount_candidates[0] || null;
                macColumn.value =
                    suggestions.mac_candidates[0] || schemaValue.mac_column;
                mecColumn.value =
                    suggestions.mec_candidates[0] || schemaValue.mec_column;
                manColumn.value = suggestions.man_candidates[0] || null;
                menColumn.value = suggestions.men_candidates[0] || null;
                mocColumn.value = suggestions.moc_candidates[0] || null;
                colaM1Column.value = suggestions.cola_m1_candidates[0] || null;
            }
        } catch (error) {
            schema.value = null;
            errorMsg.value = error instanceof Error ? error.message : String(error);
        } finally {
            schemaLoading.value = false;
        }
    }

    async function loadConfigs() {
        configsLoading.value = true;
        try {
            const result = await getDatasetConfigs();
            configs.value = result.configs;
        } catch (error) {
            console.error('Failed to load dataset configs:', error);
        } finally {
            configsLoading.value = false;
        }
    }

    watch(
        () => uploadedFile.value,
        () => {
            schema.value = null;
            errorMsg.value = null;
        },
    );

    watch(
        () => aeResults.value,
        () => {
            scatterShowOverall.value = true;
            scatterSplitVisible.value = {};
            treemapStateByTab.value = {};
        },
    );

    watch(
        () => resultsTab.value,
        (newTab) => {
            if (!aeResults.value) return;

            if (!treemapStateByTab.value[newTab]) {
                treemapStateByTab.value[newTab] = {
                    showOverall: true,
                    splitVisible: {},
                };
            }

            if (newTab === 'overall') {
                treemapStateByTab.value[newTab].showOverall = true;
                const allHidden: Record<string, boolean> = {};
                (aeResults.value.split_results || []).forEach((result) => {
                    allHidden[result.split_group] = false;
                });
                treemapStateByTab.value[newTab].splitVisible = allHidden;
                return;
            }

            if (newTab.startsWith('split-')) {
                const splitIdx = Number.parseInt(newTab.slice('split-'.length), 10);
                const splitResults = aeResults.value.split_results || [];

                if (splitIdx >= 0 && splitIdx < splitResults.length) {
                    const targetGroup = splitResults[splitIdx].split_group;
                    treemapStateByTab.value[newTab].showOverall = false;

                    const splitVisible: Record<string, boolean> = {};
                    splitResults.forEach((result) => {
                        splitVisible[result.split_group] =
                            result.split_group === targetGroup;
                    });
                    treemapStateByTab.value[newTab].splitVisible = splitVisible;
                }
            }
        },
    );

    watch(
        () => selectedConfigId.value,
        async (configId) => {
            if (!configId) {
                return;
            }

            schema.value = null;
            aeResults.value = null;
            errorMsg.value = null;
            insightsError.value = null;
            insightResults.value = null;
            uploadedFile.value = null;

            try {
                const config = await getDatasetConfig(configId);
                if (!isMortalityDatasetConfig(config)) {
                    throw new Error(
                        'Selected configuration is not a mortality A/E config.',
                    );
                }

                const mapping = config.module_config;
                policyNumberColumn.value = mapping.policy_number_column;
                faceAmountColumn.value = mapping.face_amount_column;
                macColumn.value = mapping.mac_column;
                mecColumn.value = mapping.mec_column;
                manColumn.value = mapping.man_column;
                menColumn.value = mapping.men_column;
                mocColumn.value = mapping.moc_column;
                colaM1Column.value = mapping.cola_m1_column;

                await onLoadUploadedSchema();
                await loadInsightsForConfig(configId);
            } catch (error) {
                errorMsg.value =
                    error instanceof Error
                        ? error.message
                        : 'Failed to load configuration';
            }
        },
    );

    onMounted(async () => {
        await loadConfigs();

        const configId = route.query.config;
        if (configId && typeof configId === 'string') {
            selectedConfigId.value = configId;
        }
    });

    const inputBindings = {
        selectedConfigId,
        selectedConfig,
        configOptions,
        configsLoading,
        insightsLoading,
        insightsError,
        insightResults,
        policyNumberColumn,
        faceAmountColumn,
        macColumn,
        mecColumn,
        manColumn,
        menColumn,
        mocColumn,
        colaM1Column,
        loading,
        errorMsg,
        canAnalyze,
    };

    const resultsBindings = {
        aeResults,
        resultsVariableName,
        resultsSplitVariableName,
        resultsSplitXAxisKind,
        resultsXAxisKind,
        resultsXDomain,
        resultsTab,
        colaResultsTab,
        scatterShowOverall,
        scatterSplitVisible,
        currentTreemapShowOverall,
        currentTreemapSplitVisible,
        splitTabLabel,
        formatPolynomialEquation,
    };

    const inputHandlers = {
        onAnalyze,
        applyInsightDrill,
    };

    return {
        schema,
        schemaLoading,
        inputBindings,
        resultsBindings,
        inputHandlers,
    };
}
