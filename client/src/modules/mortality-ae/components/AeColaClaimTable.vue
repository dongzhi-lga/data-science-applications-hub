<template>
    <div class="q-pa-sm">
        <div class="row q-col-gutter-md">
            <!-- Claims Count Table -->
            <div class="col-6">
                <div class="text-subtitle2 q-mb-sm">Claims Count</div>
                <q-table
                    table-class="cola-claim-table"
                    dense
                    flat
                    bordered
                    :rows="countTableRows"
                    :columns="countTableColumns"
                    row-key="x_group"
                    :rows-per-page-options="[0]"
                    hide-bottom
                >
                    <template v-slot:body="props">
                        <q-tr :props="props" :class="{ 'cola-total-row': props.row.isTotal }">
                            <q-td
                                v-for="col in props.cols"
                                :key="col.name"
                                :props="props"
                                :class="getCellClass({ col, row: props.row, value: col.value })"
                            >
                                {{ col.value }}
                            </q-td>
                        </q-tr>
                    </template>
                </q-table>
            </div>

            <!-- Claims Amount Table -->
            <div class="col-6">
                <div class="text-subtitle2 q-mb-sm">Claims Amount</div>
                <q-table
                    table-class="cola-claim-table"
                    dense
                    flat
                    bordered
                    :rows="amountTableRows"
                    :columns="amountTableColumns"
                    row-key="x_group"
                    :rows-per-page-options="[0]"
                    hide-bottom
                >
                    <template v-slot:body="props">
                        <q-tr :props="props" :class="{ 'cola-total-row': props.row.isTotal }">
                            <q-td
                                v-for="col in props.cols"
                                :key="col.name"
                                :props="props"
                                :class="getCellClass({ col, row: props.row, value: col.value })"
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
import { computed } from 'vue';
import type { QTableColumn } from 'quasar';
import type { ApiAeColaM1StackedResults } from '@/modules/mortality-ae/types';

const props = defineProps<{
    data: ApiAeColaM1StackedResults;
    variableName?: string;
}>();

const countTableColumns = computed<QTableColumn[]>(() => {
    const causes = props.data?.causes ?? [];
    
    const cols: QTableColumn[] = [
        {
            name: 'x_group',
            label: props.variableName ? `${props.variableName} Group` : 'Group',
            field: 'x_group',
            align: 'left',
            sortable: false,
        },
    ];

    // Add a column for each cause
    for (const cause of causes) {
        cols.push({
            name: `cause_${cause}`,
            label: cause,
            field: (row: any) => row.deaths_by_cause[cause] ?? 0,
            align: 'right',
            sortable: false,
            format: (val) => formatInt(Number(val)),
        });
    }

    // Add total column
    cols.push({
        name: 'total',
        label: 'Total Deaths',
        field: 'total_deaths',
        align: 'right',
        sortable: false,
        format: (val) => formatInt(Number(val)),
    });

    return cols;
});

const amountTableColumns = computed<QTableColumn[]>(() => {
    const causes = props.data?.causes ?? [];
    
    const cols: QTableColumn[] = [
        {
            name: 'x_group',
            label: props.variableName ? `${props.variableName} Group` : 'Group',
            field: 'x_group',
            align: 'left',
            sortable: false,
        },
    ];

    // Add a column for each cause
    for (const cause of causes) {
        cols.push({
            name: `cause_${cause}`,
            label: cause,
            field: (row: any) => row.amounts_by_cause[cause] ?? 0,
            align: 'right',
            sortable: false,
            format: (val) => formatInt(Number(val)),
        });
    }

    // Add total column
    cols.push({
        name: 'total',
        label: 'Total Amount',
        field: 'total_amount',
        align: 'right',
        sortable: false,
        format: (val) => formatInt(Number(val)),
    });

    // Add average column
    cols.push({
        name: 'average',
        label: 'Avg Amount',
        field: 'average_amount',
        align: 'right',
        sortable: false,
        format: (val) => formatInt(Number(val)),
    });

    return cols;
});

const countTableRows = computed(() => {
    const rows = props.data?.rows ?? [];
    const causes = props.data?.causes ?? [];

    const dataRows = rows.map((r) => {
        const deaths_by_cause: Record<string, number> = {};
        for (const cause of causes) {
            deaths_by_cause[cause] = Number(r.deaths_by_m1?.[cause] ?? 0);
        }

        return {
            x_group: r.x_group,
            total_deaths: Number(r.total_deaths),
            deaths_by_cause,
            isTotal: false,
        };
    });

    // Calculate totals for each cause
    const totalDeathsByCause: Record<string, number> = {};
    let grandTotal = 0;
    
    for (const cause of causes) {
        totalDeathsByCause[cause] = 0;
    }
    
    for (const row of dataRows) {
        for (const cause of causes) {
            totalDeathsByCause[cause] += row.deaths_by_cause[cause];
        }
        grandTotal += row.total_deaths;
    }

    // Add total row
    const totalRow = {
        x_group: 'Total',
        total_deaths: grandTotal,
        deaths_by_cause: totalDeathsByCause,
        isTotal: true,
    };

    return [...dataRows, totalRow];
});

const amountTableRows = computed(() => {
    const rows = props.data?.rows ?? [];
    const causes = props.data?.causes ?? [];

    const dataRows = rows.map((r) => {
        const amounts_by_cause: Record<string, number> = {};
        for (const cause of causes) {
            amounts_by_cause[cause] = Number(r.amounts_by_m1?.[cause] ?? 0);
        }

        const total_amount = Number(r.total_amount);
        const total_deaths = Number(r.total_deaths);
        const average_amount = total_deaths > 0 ? total_amount / total_deaths : 0;

        return {
            x_group: r.x_group,
            total_amount,
            average_amount,
            amounts_by_cause,
            isTotal: false,
        };
    });

    // Calculate totals for each cause
    const totalAmountsByCause: Record<string, number> = {};
    let grandTotalAmount = 0;
    let grandTotalDeaths = 0;
    
    for (const cause of causes) {
        totalAmountsByCause[cause] = 0;
    }
    
    for (let i = 0; i < dataRows.length; i++) {
        const row = dataRows[i];
        for (const cause of causes) {
            totalAmountsByCause[cause] += row.amounts_by_cause[cause];
        }
        grandTotalAmount += row.total_amount;
        grandTotalDeaths += Number(rows[i].total_deaths);
    }

    const grandAverage = grandTotalDeaths > 0 ? grandTotalAmount / grandTotalDeaths : 0;

    // Add total row
    const totalRow = {
        x_group: 'Total',
        total_amount: grandTotalAmount,
        average_amount: grandAverage,
        amounts_by_cause: totalAmountsByCause,
        isTotal: true,
    };

    return [...dataRows, totalRow];
});

function formatInt(x: number): string {
    return Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(x);
}

function formatDecimals(x: number, decimals: number): string {
    return Intl.NumberFormat(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    }).format(x);
}

function getCellClass(props: any): string {
    // Highlight cells based on value
    if (props.row?.isTotal) {
        return 'cola-total-cell';
    }
    if (props.col.name === 'x_group' || props.col.name === 'total') {
        return '';
    }
    const value = Number(props.value);
    if (value === 0) {
        return 'cola-cell-zero';
    }
    return '';
}
</script>

<style scoped>
.cola-claim-table tr th {
    font-size: 14px;
}

.cola-claim-table td {
    font-size: 13px;
}

.cola-cell-zero {
    color: #bbb;
}

.cola-total-row {
    font-weight: 600;
    background-color: #f5f5f5;
}

.cola-total-cell {
    font-weight: 600;
}
</style>
