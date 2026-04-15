<template>
    <div>
        <q-banner class="q-px-md q-pt-md q-pb-sm">
            <div class="row items-center q-gutter-x-sm">
                <span class="text-h4">Experience Study Mortality A/E</span>
            </div>
            <div class="text-body2 text-grey-7 q-mt-xs">
                Load a saved mortality configuration and run the Experience Study
                Mortality A/E workflow.
            </div>
        </q-banner>

        <q-card class="q-mt-md">
            <q-expansion-item
                switch-toggle-side
                label="About"
                header-class="text-primary"
            >
                <div class="q-pa-md">
                    This tool runs locally and analyzes uploaded data files (CSV, Excel,
                    Parquet). It computes A/E (Actual vs Expected) ratios across x-axis
                    groups and can optionally overlay split results on the same chart.
                </div>
            </q-expansion-item>
        </q-card>

        <q-card class="q-pa-md q-mt-md">
            <q-banner class="q-pa-sm">
                <span class="text-h5">Inputs</span>
            </q-banner>

            <form class="q-mt-sm" @submit.prevent="handlers.onAnalyze">
                <div class="row items-center q-col-gutter-md q-mb-md">
                    <div class="col-12">
                        <q-select
                            v-model="model.selectedConfigId"
                            :options="model.configOptions"
                            emit-value
                            map-options
                            outlined
                            dense
                            label="Select Saved Dataset Configuration"
                            class="input-600"
                            clearable
                            :loading="model.configsLoading"
                            hint="Choose a previously configured dataset from the Data Input page"
                        >
                            <template #prepend>
                                <q-icon name="folder_open" />
                            </template>
                        </q-select>
                    </div>
                </div>

                <div v-if="model.selectedConfig" class="q-mb-md">
                    <q-banner class="bg-green-1" dense>
                        <template #avatar>
                            <q-icon name="check_circle" color="positive" />
                        </template>
                        <strong>{{ model.selectedConfig.dataset_name }}</strong> loaded
                        successfully
                        <br />File and column mappings loaded automatically from saved
                        configuration
                    </q-banner>
                </div>

                <div v-if="!model.selectedConfig" class="q-mb-md">
                    <q-banner class="bg-grey-3" dense>
                        <template #avatar>
                            <q-icon name="info" color="grey-7" />
                        </template>
                        Please select a saved dataset configuration above, or go to the
                        <strong>Central Setup</strong> page to create a new one.
                    </q-banner>
                </div>

                <AeInsightBanner
                    v-if="model.selectedConfig"
                    class="q-mb-md"
                    :insights="model.insightResults"
                    :loading="model.insightsLoading"
                    :error="model.insightsError"
                    @apply="handlers.applyInsightDrill"
                />

                <q-card flat bordered class="q-mt-md">
                    <q-card-section class="q-pb-sm">
                        <div class="text-h6">X-axis Variable</div>
                        <div class="text-body2 text-grey-7">
                            Choose the variable to plot on the x-axis. Numeric variables can
                            be binned; date variables can be binned; categorical variables can
                            be grouped.
                        </div>
                    </q-card-section>

                    <q-card-section class="q-pt-none">
                        <div class="row items-center q-gutter-md">
                            <q-select
                                v-model="model.xVarName"
                                :options="model.xVariableOptions"
                                emit-value
                                map-options
                                outlined
                                dense
                                options-dense
                                label="X variable"
                                class="input-200"
                                :disable="!model.schema || model.schemaLoading"
                                clearable
                            />

                            <template
                                v-if="
                                    !model.isXCross &&
                                    (model.xVarInfo?.kind === 'numeric' ||
                                        model.xVarInfo?.kind === 'date')
                                "
                            >
                                <q-select
                                    v-model="model.xNumericBinning"
                                    :options="model.numericBinningOptions"
                                    emit-value
                                    map-options
                                    outlined
                                    dense
                                    options-dense
                                    label="Binning"
                                    class="input-200"
                                />
                                <q-select
                                    v-if="model.xNumericBinning !== 'custom'"
                                    v-model="model.xNumericBinCount"
                                    :options="model.binCountOptions"
                                    outlined
                                    dense
                                    options-dense
                                    emit-value
                                    map-options
                                    label="Bins"
                                    class="input-200"
                                />
                                <q-input
                                    v-else
                                    v-model="model.xNumericCustomEdgesRaw"
                                    outlined
                                    dense
                                    label="Custom edges"
                                    class="input-200"
                                />
                            </template>

                            <template
                                v-else-if="
                                    !model.isXCross && model.xVarInfo?.kind === 'categorical'
                                "
                            >
                                <q-select
                                    v-model="model.xCatGroupCount"
                                    :options="model.categoricalGroupCountOptions"
                                    emit-value
                                    map-options
                                    outlined
                                    dense
                                    options-dense
                                    label="Groups"
                                    class="input-200"
                                />
                            </template>

                            <template v-else-if="model.isXCross">
                                <q-select
                                    v-model="model.xCrossAName"
                                    :options="model.baseVariableOptions"
                                    emit-value
                                    map-options
                                    outlined
                                    dense
                                    options-dense
                                    label="Variable A"
                                    class="input-200"
                                    :disable="!model.schema || model.schemaLoading"
                                    clearable
                                />
                                <template
                                    v-if="
                                        model.xCrossAVarInfo?.kind === 'numeric' ||
                                        model.xCrossAVarInfo?.kind === 'date'
                                    "
                                >
                                    <q-select
                                        v-model="model.xCrossANumericBinning"
                                        :options="model.numericBinningOptions"
                                        emit-value
                                        map-options
                                        outlined
                                        dense
                                        options-dense
                                        label="A binning"
                                        class="input-200"
                                    />
                                    <q-select
                                        v-if="model.xCrossANumericBinning !== 'custom'"
                                        v-model="model.xCrossANumericBinCount"
                                        :options="model.binCountOptions"
                                        outlined
                                        dense
                                        options-dense
                                        emit-value
                                        map-options
                                        label="A bins"
                                        class="input-200"
                                    />
                                    <q-input
                                        v-else
                                        v-model="model.xCrossANumericCustomEdgesRaw"
                                        outlined
                                        dense
                                        label="A edges"
                                        class="input-200"
                                    />
                                </template>

                                <q-select
                                    v-model="model.xCrossBName"
                                    :options="model.baseVariableOptions"
                                    emit-value
                                    map-options
                                    outlined
                                    dense
                                    options-dense
                                    label="Variable B"
                                    class="input-200"
                                    :disable="!model.schema || model.schemaLoading"
                                    clearable
                                />
                                <template
                                    v-if="
                                        model.xCrossBVarInfo?.kind === 'numeric' ||
                                        model.xCrossBVarInfo?.kind === 'date'
                                    "
                                >
                                    <q-select
                                        v-model="model.xCrossBNumericBinning"
                                        :options="model.numericBinningOptions"
                                        emit-value
                                        map-options
                                        outlined
                                        dense
                                        options-dense
                                        label="B binning"
                                        class="input-200"
                                    />
                                    <q-select
                                        v-if="model.xCrossBNumericBinning !== 'custom'"
                                        v-model="model.xCrossBNumericBinCount"
                                        :options="model.binCountOptions"
                                        outlined
                                        dense
                                        options-dense
                                        emit-value
                                        map-options
                                        label="B bins"
                                        class="input-200"
                                    />
                                    <q-input
                                        v-else
                                        v-model="model.xCrossBNumericCustomEdgesRaw"
                                        outlined
                                        dense
                                        label="B edges"
                                        class="input-200"
                                    />
                                </template>

                                <q-select
                                    v-model="model.xCrossGroupCount"
                                    :options="model.crossGroupCountOptions"
                                    emit-value
                                    map-options
                                    outlined
                                    dense
                                    options-dense
                                    label="Groups"
                                    class="input-200"
                                    :disable="!model.xCrossAName || !model.xCrossBName"
                                />
                            </template>

                            <q-space />
                            <div
                                v-if="!model.isXCross && model.xVarInfo"
                                class="text-caption text-grey-7"
                            >
                                <span class="text-weight-medium">Type:</span>
                                {{ model.xVarInfo.kind }}
                                <template v-if="model.xVarInfo.kind === 'numeric'">
                                    <span class="text-weight-medium">Range:</span>
                                    {{ model.xVarInfo.numeric_min ?? '-' }} ->
                                    {{ model.xVarInfo.numeric_max ?? '-' }}
                                </template>
                                <template v-else-if="model.xVarInfo.kind === 'date'">
                                    <span class="text-weight-medium">Range:</span>
                                    {{ model.xVarInfo.date_min ?? '-' }} ->
                                    {{ model.xVarInfo.date_max ?? '-' }}
                                </template>
                                <template v-else>
                                    <span class="text-weight-medium">Unique:</span>
                                    {{ model.xVarInfo.unique_count ?? 'unknown' }}
                                    <span
                                        v-if="
                                            model.xVarInfo.unique_values &&
                                            model.xVarInfo.unique_count &&
                                            model.xVarInfo.unique_values.length <
                                                model.xVarInfo.unique_count
                                        "
                                    >
                                        (first {{ model.xVarInfo.unique_values.length }})
                                    </span>
                                </template>
                            </div>
                            <div v-else-if="model.isXCross" class="text-caption text-grey-7">
                                <span class="text-weight-medium">A:</span>
                                {{ model.xCrossAVarInfo?.kind ?? '-' }}
                                <template v-if="model.xCrossAVarInfo?.kind === 'numeric'">
                                    {{ model.xCrossAVarInfo.numeric_min ?? '-' }} ->
                                    {{ model.xCrossAVarInfo.numeric_max ?? '-' }}
                                </template>
                                <template v-else-if="model.xCrossAVarInfo?.kind === 'date'">
                                    {{ model.xCrossAVarInfo.date_min ?? '-' }} ->
                                    {{ model.xCrossAVarInfo.date_max ?? '-' }}
                                </template>
                                <template
                                    v-else-if="
                                        model.xCrossAVarInfo?.kind === 'categorical'
                                    "
                                >
                                    {{ model.xCrossAVarInfo.unique_count ?? 'unknown' }}
                                    unique
                                </template>
                                |
                                <span class="text-weight-medium">B:</span>
                                {{ model.xCrossBVarInfo?.kind ?? '-' }}
                                <template v-if="model.xCrossBVarInfo?.kind === 'numeric'">
                                    {{ model.xCrossBVarInfo.numeric_min ?? '-' }} ->
                                    {{ model.xCrossBVarInfo.numeric_max ?? '-' }}
                                </template>
                                <template v-else-if="model.xCrossBVarInfo?.kind === 'date'">
                                    {{ model.xCrossBVarInfo.date_min ?? '-' }} ->
                                    {{ model.xCrossBVarInfo.date_max ?? '-' }}
                                </template>
                                <template
                                    v-else-if="
                                        model.xCrossBVarInfo?.kind === 'categorical'
                                    "
                                >
                                    {{ model.xCrossBVarInfo.unique_count ?? 'unknown' }}
                                    unique
                                </template>
                                <span v-if="model.xCrossLabelsLoading">
                                    <q-spinner size="14px" class="q-ml-xs" />
                                </span>
                            </div>
                        </div>

                        <div v-if="!model.isXCross && model.xVarInfo" class="q-mt-sm">
                            <div
                                v-if="model.xVarInfo.kind === 'categorical'"
                                class="q-mt-sm"
                            >
                                <div
                                    v-if="
                                        model.xCatGroupCount !== 'all' &&
                                        !model.xCatUniqueValues
                                    "
                                    class="q-mt-sm"
                                >
                                    <q-banner class="q-pa-sm bg-orange-1 text-orange-10">
                                        This column has too many unique values to edit groups in
                                        the UI. Reduce cardinality or increase
                                        `AEMONITOR_MAX_UNIQUE_VALUES`.
                                    </q-banner>
                                </div>

                                <div
                                    v-if="
                                        model.xCatGroupCount !== 'all' &&
                                        model.xCatUniqueValues
                                    "
                                    class="q-mt-md"
                                >
                                    <div class="text-subtitle2 q-mb-sm">
                                        Group definitions (last group is Remaining)
                                    </div>

                                    <div
                                        v-for="(g, idx) in model.xCatGroups"
                                        :key="idx"
                                        class="q-mb-sm"
                                    >
                                        <div class="row items-center q-gutter-md">
                                            <q-input
                                                v-model="g.name"
                                                filled
                                                dense
                                                label="Name"
                                                class="input-200"
                                            />
                                            <q-input
                                                v-model="g.x_position"
                                                filled
                                                dense
                                                type="number"
                                                label="Pos"
                                                class="input-120"
                                                placeholder="Auto"
                                            />
                                            <q-select
                                                v-model="g.values"
                                                :options="model.xCatUniqueValues"
                                                outlined
                                                dense
                                                options-dense
                                                multiple
                                                use-chips
                                                label="Values"
                                                style="min-width: 420px; max-width: 100%"
                                            />
                                        </div>
                                    </div>

                                    <div class="q-mb-sm">
                                        <div class="row items-center q-gutter-md">
                                            <q-input
                                                v-model="model.xCatRemainingName"
                                                filled
                                                dense
                                                label="Name"
                                                class="input-200"
                                            />
                                            <q-input
                                                v-model="model.xCatRemainingPosition"
                                                filled
                                                dense
                                                type="number"
                                                label="Pos"
                                                class="input-120"
                                                placeholder="Auto"
                                            />
                                            <q-select
                                                :model-value="model.xCatRemainingValues"
                                                :options="model.xCatUniqueValues"
                                                outlined
                                                dense
                                                options-dense
                                                multiple
                                                use-chips
                                                disable
                                                label="Values"
                                                style="min-width: 420px; max-width: 100%"
                                            >
                                                <q-tooltip
                                                    v-if="model.xCatRemainingPreview"
                                                    anchor="top middle"
                                                    self="bottom middle"
                                                >
                                                    {{ model.xCatRemainingPreview }}
                                                </q-tooltip>
                                            </q-select>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div v-else-if="model.isXCross" class="q-mt-sm">
                            <div v-if="model.xCrossTooManyUniques" class="q-mt-sm">
                                <q-banner class="q-pa-sm bg-orange-1 text-orange-10">
                                    One of the selected variables has too many unique values to
                                    edit cross groups in the UI. Reduce cardinality or increase
                                    `AEMONITOR_MAX_UNIQUE_VALUES`.
                                </q-banner>
                            </div>

                            <div v-else class="q-mt-md">
                                <div class="text-subtitle2 q-mb-sm">
                                    Cross group definitions (last group is Remaining)
                                </div>

                                <div
                                    v-for="(g, idx) in model.xCrossGroups"
                                    :key="`x-cross-${idx}`"
                                    class="q-mb-sm"
                                >
                                    <div class="row items-center q-gutter-md">
                                        <q-input
                                            v-model="g.name"
                                            filled
                                            dense
                                            label="Name"
                                            class="input-200"
                                        />
                                        <q-input
                                            v-model="g.x_position"
                                            filled
                                            dense
                                            type="number"
                                            label="Pos"
                                            class="input-120"
                                            placeholder="Auto"
                                        />
                                        <q-checkbox v-model="g.a_any" dense label="Any A" />
                                        <q-select
                                            v-model="g.a_values"
                                            :options="model.xCrossALabels || []"
                                            outlined
                                            dense
                                            options-dense
                                            multiple
                                            use-chips
                                            label="A values"
                                            :disable="g.a_any || !model.xCrossALabels"
                                            style="min-width: 320px; max-width: 100%"
                                        />
                                        <q-checkbox v-model="g.b_any" dense label="Any B" />
                                        <q-select
                                            v-model="g.b_values"
                                            :options="model.xCrossBLabels || []"
                                            outlined
                                            dense
                                            options-dense
                                            multiple
                                            use-chips
                                            label="B values"
                                            :disable="g.b_any || !model.xCrossBLabels"
                                            style="min-width: 320px; max-width: 100%"
                                        />
                                    </div>
                                    <div
                                        v-if="g.a_any && g.b_any"
                                        class="text-negative text-caption q-mt-xs"
                                    >
                                        A group cannot be both Any A and Any B.
                                    </div>
                                </div>

                                <div class="q-mb-sm">
                                    <div class="row items-center q-gutter-md">
                                        <q-input
                                            v-model="model.xCrossRemainingName"
                                            filled
                                            dense
                                            label="Name"
                                            class="input-200"
                                        />
                                        <q-input
                                            v-model="model.xCrossRemainingPosition"
                                            filled
                                            dense
                                            type="number"
                                            label="Pos"
                                            class="input-120"
                                            placeholder="Auto"
                                        />
                                        <q-banner class="q-pa-xs bg-grey-1 text-grey-8">
                                            Remaining = everything not matched by earlier groups
                                        </q-banner>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>

                <q-card flat bordered class="q-mt-md">
                    <q-card-section class="q-pb-sm">
                        <div class="text-h6">Split Variable (optional)</div>
                        <div class="text-body2 text-grey-7">
                            Optionally split results into multiple series by a second
                            variable. Configure binning/grouping the same way.
                        </div>
                    </q-card-section>

                    <q-card-section class="q-pt-none">
                        <div class="row items-center q-gutter-md">
                            <q-select
                                v-model="model.splitVarName"
                                :options="model.splitVariableOptions"
                                emit-value
                                map-options
                                outlined
                                dense
                                options-dense
                                label="Split variable"
                                class="input-200"
                                :disable="!model.schema || model.schemaLoading"
                                clearable
                            />

                            <template
                                v-if="
                                    !model.isSplitCross &&
                                    (model.splitVarInfo?.kind === 'numeric' ||
                                        model.splitVarInfo?.kind === 'date')
                                "
                            >
                                <q-select
                                    v-model="model.splitNumericBinning"
                                    :options="model.numericBinningOptions"
                                    emit-value
                                    map-options
                                    outlined
                                    dense
                                    options-dense
                                    label="Binning"
                                    class="input-200"
                                />
                                <q-select
                                    v-if="model.splitNumericBinning !== 'custom'"
                                    v-model="model.splitNumericBinCount"
                                    :options="model.binCountOptions"
                                    outlined
                                    dense
                                    options-dense
                                    emit-value
                                    map-options
                                    label="Bins"
                                    class="input-200"
                                />
                                <q-input
                                    v-else
                                    v-model="model.splitNumericCustomEdgesRaw"
                                    outlined
                                    dense
                                    label="Custom edges"
                                    class="input-200"
                                />
                            </template>

                            <template
                                v-else-if="
                                    !model.isSplitCross &&
                                    model.splitVarInfo?.kind === 'categorical'
                                "
                            >
                                <q-select
                                    v-model="model.splitCatGroupCount"
                                    :options="model.splitCategoricalGroupCountOptions"
                                    emit-value
                                    map-options
                                    outlined
                                    dense
                                    options-dense
                                    label="Groups"
                                    class="input-200"
                                />
                            </template>

                            <template v-else-if="model.isSplitCross">
                                <q-select
                                    v-model="model.splitCrossAName"
                                    :options="model.baseVariableOptions"
                                    emit-value
                                    map-options
                                    outlined
                                    dense
                                    options-dense
                                    label="Variable A"
                                    class="input-200"
                                    :disable="!model.schema || model.schemaLoading"
                                    clearable
                                />
                                <template
                                    v-if="
                                        model.splitCrossAVarInfo?.kind === 'numeric' ||
                                        model.splitCrossAVarInfo?.kind === 'date'
                                    "
                                >
                                    <q-select
                                        v-model="model.splitCrossANumericBinning"
                                        :options="model.numericBinningOptions"
                                        emit-value
                                        map-options
                                        outlined
                                        dense
                                        options-dense
                                        label="A binning"
                                        class="input-200"
                                    />
                                    <q-select
                                        v-if="model.splitCrossANumericBinning !== 'custom'"
                                        v-model="model.splitCrossANumericBinCount"
                                        :options="model.binCountOptions"
                                        outlined
                                        dense
                                        options-dense
                                        emit-value
                                        map-options
                                        label="A bins"
                                        class="input-200"
                                    />
                                    <q-input
                                        v-else
                                        v-model="model.splitCrossANumericCustomEdgesRaw"
                                        outlined
                                        dense
                                        label="A edges"
                                        class="input-200"
                                    />
                                </template>

                                <q-select
                                    v-model="model.splitCrossBName"
                                    :options="model.baseVariableOptions"
                                    emit-value
                                    map-options
                                    outlined
                                    dense
                                    options-dense
                                    label="Variable B"
                                    class="input-200"
                                    :disable="!model.schema || model.schemaLoading"
                                    clearable
                                />
                                <template
                                    v-if="
                                        model.splitCrossBVarInfo?.kind === 'numeric' ||
                                        model.splitCrossBVarInfo?.kind === 'date'
                                    "
                                >
                                    <q-select
                                        v-model="model.splitCrossBNumericBinning"
                                        :options="model.numericBinningOptions"
                                        emit-value
                                        map-options
                                        outlined
                                        dense
                                        options-dense
                                        label="B binning"
                                        class="input-200"
                                    />
                                    <q-select
                                        v-if="model.splitCrossBNumericBinning !== 'custom'"
                                        v-model="model.splitCrossBNumericBinCount"
                                        :options="model.binCountOptions"
                                        outlined
                                        dense
                                        options-dense
                                        emit-value
                                        map-options
                                        label="B bins"
                                        class="input-200"
                                    />
                                    <q-input
                                        v-else
                                        v-model="model.splitCrossBNumericCustomEdgesRaw"
                                        outlined
                                        dense
                                        label="B edges"
                                        class="input-200"
                                    />
                                </template>

                                <q-select
                                    v-model="model.splitCrossGroupCount"
                                    :options="model.crossGroupCountOptions"
                                    emit-value
                                    map-options
                                    outlined
                                    dense
                                    options-dense
                                    label="Groups"
                                    class="input-200"
                                    :disable="
                                        !model.splitCrossAName || !model.splitCrossBName
                                    "
                                />
                            </template>

                            <q-space />
                            <div
                                v-if="!model.isSplitCross && model.splitVarInfo"
                                class="text-caption text-grey-7"
                            >
                                <span class="text-weight-medium">Type:</span>
                                {{ model.splitVarInfo.kind }}
                                <template v-if="model.splitVarInfo.kind === 'numeric'">
                                    <span class="text-weight-medium">Range:</span>
                                    {{ model.splitVarInfo.numeric_min ?? '-' }} ->
                                    {{ model.splitVarInfo.numeric_max ?? '-' }}
                                </template>
                                <template v-else-if="model.splitVarInfo.kind === 'date'">
                                    <span class="text-weight-medium">Range:</span>
                                    {{ model.splitVarInfo.date_min ?? '-' }} ->
                                    {{ model.splitVarInfo.date_max ?? '-' }}
                                </template>
                                <template v-else>
                                    <span class="text-weight-medium">Unique:</span>
                                    {{ model.splitVarInfo.unique_count ?? 'unknown' }}
                                    <span
                                        v-if="
                                            model.splitVarInfo.unique_values &&
                                            model.splitVarInfo.unique_count &&
                                            model.splitVarInfo.unique_values.length <
                                                model.splitVarInfo.unique_count
                                        "
                                    >
                                        (first
                                        {{ model.splitVarInfo.unique_values.length }})
                                    </span>
                                </template>
                            </div>
                            <div
                                v-else-if="model.isSplitCross"
                                class="text-caption text-grey-7"
                            >
                                <span class="text-weight-medium">A:</span>
                                {{ model.splitCrossAVarInfo?.kind ?? '-' }}
                                <template
                                    v-if="model.splitCrossAVarInfo?.kind === 'numeric'"
                                >
                                    {{ model.splitCrossAVarInfo.numeric_min ?? '-' }} ->
                                    {{ model.splitCrossAVarInfo.numeric_max ?? '-' }}
                                </template>
                                <template
                                    v-else-if="model.splitCrossAVarInfo?.kind === 'date'"
                                >
                                    {{ model.splitCrossAVarInfo.date_min ?? '-' }} ->
                                    {{ model.splitCrossAVarInfo.date_max ?? '-' }}
                                </template>
                                <template
                                    v-else-if="
                                        model.splitCrossAVarInfo?.kind === 'categorical'
                                    "
                                >
                                    {{ model.splitCrossAVarInfo.unique_count ?? 'unknown' }}
                                    unique
                                </template>
                                |
                                <span class="text-weight-medium">B:</span>
                                {{ model.splitCrossBVarInfo?.kind ?? '-' }}
                                <template
                                    v-if="model.splitCrossBVarInfo?.kind === 'numeric'"
                                >
                                    {{ model.splitCrossBVarInfo.numeric_min ?? '-' }} ->
                                    {{ model.splitCrossBVarInfo.numeric_max ?? '-' }}
                                </template>
                                <template
                                    v-else-if="model.splitCrossBVarInfo?.kind === 'date'"
                                >
                                    {{ model.splitCrossBVarInfo.date_min ?? '-' }} ->
                                    {{ model.splitCrossBVarInfo.date_max ?? '-' }}
                                </template>
                                <template
                                    v-else-if="
                                        model.splitCrossBVarInfo?.kind === 'categorical'
                                    "
                                >
                                    {{ model.splitCrossBVarInfo.unique_count ?? 'unknown' }}
                                    unique
                                </template>
                                <span v-if="model.splitCrossLabelsLoading">
                                    <q-spinner size="14px" class="q-ml-xs" />
                                </span>
                            </div>
                        </div>

                        <div
                            v-if="!model.isSplitCross && model.splitVarInfo"
                            class="q-mt-sm"
                        >
                            <div
                                v-if="model.splitVarInfo.kind === 'categorical'"
                                class="q-mt-sm"
                            >
                                <div
                                    v-if="
                                        model.splitCatGroupCount !== 'all' &&
                                        !model.splitCatUniqueValues
                                    "
                                    class="q-mt-sm"
                                >
                                    <q-banner class="q-pa-sm bg-orange-1 text-orange-10">
                                        This column has too many unique values to edit groups in
                                        the UI. Reduce cardinality or increase
                                        `AEMONITOR_MAX_UNIQUE_VALUES`.
                                    </q-banner>
                                </div>

                                <div
                                    v-if="
                                        model.splitCatGroupCount !== 'all' &&
                                        model.splitCatUniqueValues
                                    "
                                    class="q-mt-md"
                                >
                                    <div class="text-subtitle2 q-mb-sm">
                                        Group definitions (last group is Remaining)
                                    </div>

                                    <div
                                        v-for="(g, idx) in model.splitCatGroups"
                                        :key="idx"
                                        class="q-mb-sm"
                                    >
                                        <div class="row items-center q-gutter-md">
                                            <q-input
                                                v-model="g.name"
                                                filled
                                                dense
                                                label="Name"
                                                class="input-200"
                                            />
                                            <q-input
                                                v-model="g.x_position"
                                                filled
                                                dense
                                                type="number"
                                                label="Pos"
                                                class="input-120"
                                                placeholder="Auto"
                                            />
                                            <q-select
                                                v-model="g.values"
                                                :options="model.splitCatUniqueValues"
                                                outlined
                                                dense
                                                options-dense
                                                multiple
                                                use-chips
                                                label="Values"
                                                style="min-width: 420px; max-width: 100%"
                                            />
                                        </div>
                                    </div>

                                    <div class="q-mb-sm">
                                        <div class="row items-center q-gutter-md">
                                            <q-input
                                                v-model="model.splitCatRemainingName"
                                                filled
                                                dense
                                                label="Name"
                                                class="input-200"
                                            />
                                            <q-input
                                                v-model="model.splitCatRemainingPosition"
                                                filled
                                                dense
                                                type="number"
                                                label="Pos"
                                                class="input-120"
                                                placeholder="Auto"
                                            />
                                            <q-select
                                                :model-value="model.splitCatRemainingValues"
                                                :options="model.splitCatUniqueValues"
                                                outlined
                                                dense
                                                options-dense
                                                multiple
                                                use-chips
                                                disable
                                                label="Values"
                                                style="min-width: 420px; max-width: 100%"
                                            >
                                                <q-tooltip
                                                    v-if="model.splitCatRemainingPreview"
                                                    anchor="top middle"
                                                    self="bottom middle"
                                                >
                                                    {{ model.splitCatRemainingPreview }}
                                                </q-tooltip>
                                            </q-select>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-else-if="model.isSplitCross" class="q-mt-sm">
                            <div v-if="model.splitCrossTooManyUniques" class="q-mt-sm">
                                <q-banner class="q-pa-sm bg-orange-1 text-orange-10">
                                    One of the selected variables has too many unique values to
                                    edit cross groups in the UI. Reduce cardinality or increase
                                    `AEMONITOR_MAX_UNIQUE_VALUES`.
                                </q-banner>
                            </div>

                            <div v-else class="q-mt-md">
                                <div class="text-subtitle2 q-mb-sm">
                                    Cross group definitions (last group is Remaining)
                                </div>

                                <div
                                    v-for="(g, idx) in model.splitCrossGroups"
                                    :key="`split-cross-${idx}`"
                                    class="q-mb-sm"
                                >
                                    <div class="row items-center q-gutter-md">
                                        <q-input
                                            v-model="g.name"
                                            filled
                                            dense
                                            label="Name"
                                            class="input-200"
                                        />
                                        <q-input
                                            v-model="g.x_position"
                                            filled
                                            dense
                                            type="number"
                                            label="Pos"
                                            class="input-120"
                                            placeholder="Auto"
                                        />
                                        <q-checkbox v-model="g.a_any" dense label="Any A" />
                                        <q-select
                                            v-model="g.a_values"
                                            :options="model.splitCrossALabels || []"
                                            outlined
                                            dense
                                            options-dense
                                            multiple
                                            use-chips
                                            label="A values"
                                            :disable="g.a_any || !model.splitCrossALabels"
                                            style="min-width: 320px; max-width: 100%"
                                        />
                                        <q-checkbox v-model="g.b_any" dense label="Any B" />
                                        <q-select
                                            v-model="g.b_values"
                                            :options="model.splitCrossBLabels || []"
                                            outlined
                                            dense
                                            options-dense
                                            multiple
                                            use-chips
                                            label="B values"
                                            :disable="g.b_any || !model.splitCrossBLabels"
                                            style="min-width: 320px; max-width: 100%"
                                        />
                                    </div>
                                    <div
                                        v-if="g.a_any && g.b_any"
                                        class="text-negative text-caption q-mt-xs"
                                    >
                                        A group cannot be both Any A and Any B.
                                    </div>
                                </div>

                                <div class="q-mb-sm">
                                    <div class="row items-center q-gutter-md">
                                        <q-input
                                            v-model="model.splitCrossRemainingName"
                                            filled
                                            dense
                                            label="Name"
                                            class="input-200"
                                        />
                                        <q-input
                                            v-model="model.splitCrossRemainingPosition"
                                            filled
                                            dense
                                            type="number"
                                            label="Pos"
                                            class="input-120"
                                            placeholder="Auto"
                                        />
                                        <q-banner class="q-pa-xs bg-grey-1 text-grey-8">
                                            Remaining = everything not matched by earlier groups
                                        </q-banner>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>

                <q-card v-if="model.polyFitEligible" flat bordered class="q-mt-md">
                    <q-card-section class="q-pb-sm">
                        <div class="text-h6">Polynomial Best Fit (optional)</div>
                        <div class="text-body2 text-grey-7">
                            Optionally configure a simple polynomial best-fit for the plotted
                            relationship.
                        </div>
                    </q-card-section>

                    <q-card-section class="q-pt-none">
                        <div class="row items-center q-gutter-md">
                            <q-checkbox
                                v-model="model.polyEnabled"
                                dense
                                label="Enable polynomial fit"
                            />
                            <q-select
                                v-model="model.polyDegree"
                                :options="model.polyDegreeOptions"
                                outlined
                                dense
                                options-dense
                                emit-value
                                map-options
                                label="Degree"
                                class="input-200"
                                :disable="!model.polyEnabled"
                            />
                            <q-checkbox
                                v-model="model.polyWeighted"
                                dense
                                label="Weighted fit"
                                :disable="!model.polyEnabled"
                            />
                        </div>
                    </q-card-section>
                </q-card>

                <div class="row items-center q-gutter-sm q-mt-md">
                    <q-btn
                        label="Analyze"
                        type="submit"
                        color="primary"
                        :disable="!model.canAnalyze || model.loading"
                        :loading="model.loading"
                    />
                    <div v-if="model.errorMsg" class="text-negative">
                        {{ model.errorMsg }}
                    </div>
                </div>
            </form>
        </q-card>
    </div>
</template>

<script setup lang="ts">
import AeInsightBanner from './AeInsightBanner.vue';

defineProps<{
    model: Record<string, any>;
    handlers: Record<string, any>;
}>();
</script>

<style scoped>
.input-200 {
    width: 200px;
    max-width: 100%;
}

.input-600 {
    width: 600px;
    max-width: 100%;
}

.input-120 {
    width: 120px;
    max-width: 100%;
}
</style>
