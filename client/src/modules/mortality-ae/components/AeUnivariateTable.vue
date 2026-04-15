<template>
    <div class="q-pa-sm">
        <div class="row q-col-gutter-md">
            <!-- A/E by Count Table -->
            <div class="col-6">
                <div class="text-subtitle2 q-mb-sm">A/E by Count</div>
                <q-table
                    table-class="stats-table"
                    dense
                    flat
                    bordered
                    :rows="rows"
                    :columns="countColumns"
                    row-key="variable_group"
                    :rows-per-page-options="[0]"
                    hide-bottom
                >
                    <template v-slot:body="props">
                        <q-tr :props="props" :class="{ 'total-row': props.row.variable_group === 'Total' }">
                            <q-td
                                v-for="col in props.cols"
                                :key="col.name"
                                :props="props"
                            >
                                {{ col.value }}
                            </q-td>
                        </q-tr>
                    </template>
                </q-table>
            </div>

            <!-- A/E by Amount Table -->
            <div class="col-6">
                <div class="text-subtitle2 q-mb-sm">A/E by Amount</div>
                <q-table
                    table-class="stats-table"
                    dense
                    flat
                    bordered
                    :rows="rows"
                    :columns="amountColumns"
                    row-key="variable_group"
                    :rows-per-page-options="[0]"
                    hide-bottom
                >
                    <template v-slot:body="props">
                        <q-tr :props="props" :class="{ 'total-row': props.row.variable_group === 'Total' }">
                            <q-td
                                v-for="col in props.cols"
                                :key="col.name"
                                :props="props"
                            >
                                {{ col.value }}
                            </q-td>
                        </q-tr>
                    </template>
                </q-table>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar';

import type { ApiAeUnivariateRow } from '@/modules/mortality-ae/types';
import { formatDateTimeSeconds, formatNumericForVariable } from '@/utils/format';

const props = defineProps<{
    rows: ApiAeUnivariateRow[];
    variableName: string;
    xAxisKind: 'numeric' | 'date' | 'categorical';
}>();

const countColumns: QTableColumn<ApiAeUnivariateRow>[] = [
    {
        name: 'variable_group',
        label: props.xAxisKind === 'categorical' ? 'Group' : `${props.variableName} group`,
        field: 'variable_group',
        align: 'left',
        sortable: false,
    },
    ...(props.xAxisKind === 'numeric' || props.xAxisKind === 'date'
        ? ([
              {
                  name: 'avg_x',
                  label: `Average ${props.variableName}`,
                  field: 'avg_x',
                  align: 'right',
                  sortable: false,
                  format: (val) =>
                      val === null || val === undefined
                          ? '—'
                          : props.xAxisKind === 'date'
                            ? formatDateTimeSeconds(Number(val))
                            : formatNumericForVariable(props.variableName, Number(val)),
              },
          ] as QTableColumn<ApiAeUnivariateRow>[])
        : []),
    {
        name: 'sample_size',
        label: 'Policy Count',
        field: 'sample_size',
        align: 'right',
        sortable: false,
        format: (val) => formatInt(Number(val)),
    },
    {
        name: 'deaths',
        label: 'Claims Count (MAC)',
        field: 'deaths',
        align: 'right',
        sortable: false,
        format: (val) => formatInt(Number(val)),
    },
    {
        name: 'expected_count',
        label: 'Expected by Count (MEC)',
        field: 'expected_count',
        align: 'right',
        sortable: false,
        format: (val) => formatInt(Number(val)),
    },
    {
        name: 'ae',
        label: 'A/E by Count',
        field: 'ae',
        align: 'right',
        sortable: false,
        format: (val) => formatAe(val === null ? null : Number(val)),
    },
];

const amountColumns: QTableColumn<ApiAeUnivariateRow>[] = [
    {
        name: 'variable_group',
        label: props.xAxisKind === 'categorical' ? 'Group' : `${props.variableName} group`,
        field: 'variable_group',
        align: 'left',
        sortable: false,
    },
    ...(props.xAxisKind === 'numeric' || props.xAxisKind === 'date'
        ? ([
              {
                  name: 'avg_x',
                  label: `Average ${props.variableName}`,
                  field: 'avg_x',
                  align: 'right',
                  sortable: false,
                  format: (val) =>
                      val === null || val === undefined
                          ? '—'
                          : props.xAxisKind === 'date'
                            ? formatDateTimeSeconds(Number(val))
                            : formatNumericForVariable(props.variableName, Number(val)),
              },
          ] as QTableColumn<ApiAeUnivariateRow>[])
        : []),
    {
        name: 'total_face_amount',
        label: 'Total Face Amount',
        field: 'total_face_amount',
        align: 'right',
        sortable: false,
        format: (val) => {
            const num = Number(val);
            return Number.isFinite(num) ? formatInt(num) : '0';
        },
    },
    {
        name: 'actual_amount',
        label: 'Claims Amount (MAN)',
        field: 'actual_amount',
        align: 'right',
        sortable: false,
        format: (val) => formatDecimals(Number(val), 0),
    },
    {
        name: 'expected_amount',
        label: 'Expected by Amount (MEN)',
        field: 'expected_amount',
        align: 'right',
        sortable: false,
        format: (val) => formatDecimals(Number(val), 0),
    },
    {
        name: 'ae_amount',
        label: 'A/E by Amount',
        field: 'ae_amount',
        align: 'right',
        sortable: false,
        format: (val) => formatAe(val === null ? null : Number(val)),
    },
];

function formatInt(x: number): string {
    return Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(x);
}

function formatDecimals(x: number, decimals: number): string {
    return Intl.NumberFormat(undefined, { 
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals 
    }).format(x);
}

function formatAe(x: number | null): string {
    if (x === null || !Number.isFinite(x)) return '—';
    return Intl.NumberFormat(undefined, { 
        minimumFractionDigits: 1,
        maximumFractionDigits: 1 
    }).format(x * 100) + '%';
}
</script>

<style>
.stats-table tr th {
    font-size: 14px;
}
.stats-table td {
    font-size: 13px;
}
.total-row {
    font-weight: 600;
    background-color: #f5f5f5;
}
</style>
