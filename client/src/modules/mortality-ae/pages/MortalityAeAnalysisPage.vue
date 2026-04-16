<template>
    <q-page class="q-pa-md">
        <div class="main-container">
            <MortalityAeInputPanel
                :model="inputModel"
                :handlers="analysis.inputHandlers"
            />
            <MortalityAeResultsPanel
                v-if="resultsModel.aeResults"
                :model="resultsModel"
                :handlers="analysis.inputHandlers"
            />
        </div>
    </q-page>
</template>

<script setup lang="ts">
import { proxyRefs } from 'vue';
import { useRoute } from 'vue-router';

import MortalityAeInputPanel from '@/modules/mortality-ae/components/MortalityAeInputPanel.vue';
import MortalityAeResultsPanel from '@/modules/mortality-ae/components/MortalityAeResultsPanel.vue';
import { useMortalityAeAnalysisState } from '@/modules/mortality-ae/composables/useMortalityAeAnalysisState';
import {
    type MortalityAeVariableBuilder,
    useMortalityAeVariableBuilder,
} from '@/modules/mortality-ae/composables/useMortalityAeVariableBuilder';

const route = useRoute();

let variables: MortalityAeVariableBuilder | null = null;

const analysis = useMortalityAeAnalysisState({
    route,
    getVariables: () => variables,
});

variables = useMortalityAeVariableBuilder({
    schema: analysis.schema,
});

const sharedBindings = {
    ...analysis.inputBindings,
    schema: analysis.schema,
    schemaLoading: analysis.schemaLoading,
    ...variables.inputBindings,
};

const inputModel = proxyRefs(sharedBindings);

const resultsModel = proxyRefs({
    ...analysis.resultsBindings,
    ...sharedBindings,
});
</script>

<style scoped>
.main-container {
    width: 100%;
    max-width: 100%;
}
</style>
