export type ApiNumericBinning = 'uniform' | 'quintile' | 'custom';

export interface ApiAeXVariableNumeric {
    kind: 'numeric';
    name: string;
    binning: ApiNumericBinning;
    bin_count?: number | null;
    custom_edges?: number[] | null;
}

export interface ApiAeXVariableDate {
    kind: 'date';
    name: string;
    binning: ApiNumericBinning;
    bin_count?: number | null;
    custom_edges?: string[] | null;
}

export interface ApiCategoricalGroupDefinition {
    name: string;
    values: string[];
    x_position?: number | null;
}

export interface ApiAeXVariableCategorical {
    kind: 'categorical';
    name: string;
    grouping: 'all_unique' | 'custom';
    groups?: ApiCategoricalGroupDefinition[] | null;
    remaining_name?: string;
    remaining_position?: number | null;
}

export type ApiAeAtomicVariable =
    | ApiAeXVariableNumeric
    | ApiAeXVariableDate
    | ApiAeXVariableCategorical;

export interface ApiAeCrossGroupDefinition {
    name: string;
    a_any: boolean;
    a_values: string[];
    b_any: boolean;
    b_values: string[];
    x_position?: number | null;
}

export interface ApiAeXVariableCross {
    kind: 'cross';
    a_variable: ApiAeAtomicVariable;
    b_variable: ApiAeAtomicVariable;
    groups?: ApiAeCrossGroupDefinition[] | null;
    remaining_name?: string;
    remaining_position?: number | null;
}

export type ApiAeXVariable = ApiAeAtomicVariable | ApiAeXVariableCross;

export interface ApiColumnMapping {
    policy_number_column?: string | null;
    face_amount_column?: string | null;
    mac_column?: string | null;
    mec_column?: string | null;
    man_column?: string | null;
    men_column?: string | null;
    moc_column?: string | null;
    cola_m1_column?: string | null;
}

export interface ApiAeUnivariateParameters {
    dataset_name: string;
    x_variable: ApiAeXVariable;
    split_variable?: ApiAeXVariable | null;
    application_id_column?: string | null;
    column_mapping?: ApiColumnMapping | null;
    exclusions?: ApiAeExclusions | null;
    poly_fit?: ApiAePolynomialFitParameters | null;
}

export interface ApiAeUnivariateFromConfigParameters {
    config_id: string;
    x_variable: ApiAeXVariable;
    split_variable?: ApiAeXVariable | null;
    application_id_column?: string | null;
    exclusions?: ApiAeExclusions | null;
    poly_fit?: ApiAePolynomialFitParameters | null;
}

export interface ApiAeUnivariateRow {
    variable_group: string;
    avg_x?: number | null;
    x_coord?: number | null;
    sample_size: number;
    deaths: number;
    expected_count: number;
    actual_amount: number;
    expected_amount: number;
    exposure_count: number;
    total_face_amount: number;
    ae: number | null;
    ae_amount: number | null;
    ae_ci_lower?: number | null;
    ae_ci_upper?: number | null;
    ae_amount_ci_lower?: number | null;
    ae_amount_ci_upper?: number | null;
}

export interface ApiAeColaM1StackedRow {
    x_group: string;
    total_deaths: number;
    deaths_by_m1: Record<string, number>;
    total_amount: number;
    amounts_by_m1: Record<string, number>;
}

export interface ApiAeColaM1StackedResults {
    causes: string[];
    rows: ApiAeColaM1StackedRow[];
    total_deaths: number;
    total_amount: number;
}

export interface ApiAeUnivariateResults {
    rows: ApiAeUnivariateRow[];
    split_results?: ApiAeUnivariateSplitResults[] | null;
    poly_fit?: ApiAePolynomialFitResults | null;
    cola_m1_stacked?: ApiAeColaM1StackedResults | null;
}

export interface ApiAeUnivariateSplitResults {
    split_group: string;
    rows: ApiAeUnivariateRow[];
    poly_fit?: ApiAePolynomialFitResults | null;
    cola_m1_stacked?: ApiAeColaM1StackedResults | null;
}

export interface ApiAeExclusions {
    exclude_cola_m1: string[];
    exclude_cola_m2_by_m1: Record<string, string[]>;
}

export interface ApiAePolynomialFitParameters {
    degree: 1 | 2 | 3;
    weighted: boolean;
}

export interface ApiAePolynomialFitResults {
    degree: 1 | 2 | 3;
    weighted: boolean;
    coefficients: number[];
    r2?: number | null;
    fit_table: {
        columns: Array<{ name: string; format: 'number' | 'percent' }>;
        rows: Array<Array<number | null>>;
    };
}

export interface ApiAeInsightDrill {
    x_variable: ApiAeAtomicVariable;
    split_variable?: ApiAeAtomicVariable | null;
}

export interface ApiAeInsightResult {
    dimensions: string[];
    segment_label: string;
    segment_filters: Record<string, string>;
    sample_size: number;
    exposure_count: number;
    actual_count: number;
    expected_count: number;
    variance_count: number;
    ae_count: number | null;
    actual_amount: number;
    expected_amount: number;
    variance_amount: number;
    ae_amount: number | null;
    drill: ApiAeInsightDrill;
}

export interface ApiAeInsightsResults {
    config_id: string;
    count_insights: ApiAeInsightResult[];
    amount_insights: ApiAeInsightResult[];
}
