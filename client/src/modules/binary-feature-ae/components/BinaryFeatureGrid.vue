<template>
    <q-table
        v-model:selected="selectedRowsModel"
        v-model:pagination="pagination"
        dense
        flat
        bordered
        row-key="row_id"
        selection="multiple"
        :rows="rows"
        :columns="columns"
        :rows-per-page-options="[10, 25, 50, 100]"
        @row-click="onRowClick"
    />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { QTableColumn, QTableProps } from 'quasar';

import type {
    ApiBinaryFeatureRow,
    BinaryFeatureCiLevel,
} from '@/types/binary-feature-ae';
import {
    formatCurrency,
    formatPercentFromRatio,
    formatWholeNumber,
} from '@/utils/format';

const props = defineProps<{
    rows: ApiBinaryFeatureRow[];
    perspective: 'count' | 'amount';
    ciLevel: BinaryFeatureCiLevel;
    selectedRowIds: string[];
}>();

const emit = defineEmits<{
    'update:selectedRowIds': [value: string[]];
    'focus-row': [rowId: string];
}>();

const pagination = ref<QTableProps['pagination']>({
    page: 1,
    sortBy: 'ae_ratio',
    descending: true,
    rowsPerPage: 10,
});

const perspectiveLabel = computed(() =>
    props.perspective === 'count' ? 'Count' : 'Amount',
);

const columns = computed<QTableColumn<ApiBinaryFeatureRow>[]>(() => {
    const activeMaterialityColumn: QTableColumn<ApiBinaryFeatureRow> =
        props.perspective === 'count'
            ? {
                  name: 'claim_count',
                  label: 'Claim Count',
                  field: 'claim_count',
                  align: 'right',
                  sortable: true,
                  format: (value: number) => formatWholeNumber(value),
              }
            : {
                  name: 'man_sum',
                  label: 'MAN Sum',
                  field: 'man_sum',
                  align: 'right',
                  sortable: true,
                  format: (value: number) => formatCurrency(value),
              };

    return [
        {
            name: 'rule',
            label: 'Rule',
            field: 'rule',
            align: 'left',
            sortable: true,
        },
        {
            name: 'RuleName',
            label: 'Rule Name',
            field: 'RuleName',
            align: 'left',
            sortable: true,
        },
        {
            name: 'category',
            label: 'Category',
            field: 'category',
            align: 'left',
            sortable: true,
        },
        {
            name: 'hit_count',
            label: 'Hit Count',
            field: 'hit_count',
            align: 'right',
            sortable: true,
            format: (value: number) => formatWholeNumber(value),
        },
        {
            name: 'hit_rate',
            label: 'Hit Rate',
            field: 'hit_rate',
            align: 'right',
            sortable: true,
            format: (value: number) => formatPercentFromRatio(value),
        },
        activeMaterialityColumn,
        {
            name: 'ae_ratio',
            label: `${perspectiveLabel.value} A/E Ratio`,
            field: 'ae_ratio',
            align: 'right',
            sortable: true,
            format: (value: number) => value.toFixed(4),
        },
        {
            name: 'ci_lower',
            label: `${perspectiveLabel.value} CI Lower (${props.ciLevel}%)`,
            field: 'ci_lower',
            align: 'right',
            sortable: true,
            format: (value: number) => value.toFixed(4),
        },
        {
            name: 'ci_upper',
            label: `${perspectiveLabel.value} CI Upper (${props.ciLevel}%)`,
            field: 'ci_upper',
            align: 'right',
            sortable: true,
            format: (value: number) => value.toFixed(4),
        },
        {
            name: 'significance_class',
            label: 'Significance',
            field: 'significance_class',
            align: 'left',
            sortable: true,
        },
        {
            name: 'dominant_cola',
            label: `Dominant ${perspectiveLabel.value} Mix`,
            field: 'dominant_cola',
            align: 'left',
            sortable: true,
        },
    ];
});

watch(
    () => props.perspective,
    (nextPerspective) => {
        const currentPagination = pagination.value;
        if (!currentPagination) {
            return;
        }

        if (
            nextPerspective === 'amount' &&
            ['claim_count', 'impact_score'].includes(String(currentPagination.sortBy))
        ) {
            pagination.value = {
                ...currentPagination,
                sortBy: 'ae_ratio',
                descending: true,
            };
        }

        if (
            nextPerspective === 'count' &&
            ['man_sum', 'impact_score'].includes(String(currentPagination.sortBy))
        ) {
            pagination.value = {
                ...currentPagination,
                sortBy: 'ae_ratio',
                descending: true,
            };
        }
    },
);

const selectedRowsModel = computed<ApiBinaryFeatureRow[]>({
    get() {
        return props.rows.filter((row) => props.selectedRowIds.includes(row.row_id));
    },
    set(rows) {
        emit(
            'update:selectedRowIds',
            rows.map((row) => row.row_id),
        );
    },
});

function onRowClick(_event: Event, row: ApiBinaryFeatureRow) {
    emit('focus-row', row.row_id);
}
</script>
