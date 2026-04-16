export type NumericFormatSpec = {
    maxFractionDigits: number;
    roundingIncrement?: number;
};

function normalizeVarName(name: string): string {
    return String(name || '')
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '');
}

function getNumericFormatSpec(variableName: string): NumericFormatSpec {
    const n = normalizeVarName(variableName);

    if (n === 'age') {
        return { maxFractionDigits: 1, roundingIncrement: 0.1 };
    }
    if (n.startsWith('face')) {
        return { maxFractionDigits: 0 };
    }

    return { maxFractionDigits: 2 };
}

function applyRoundingIncrement(value: number, increment: number): number {
    if (!Number.isFinite(increment) || increment <= 0) return value;
    const scaled = value / increment;
    return Math.round(scaled) * increment;
}

export function formatNumericForVariable(
    variableName: string,
    value: number,
): string {
    if (!Number.isFinite(value)) return '—';
    const spec = getNumericFormatSpec(variableName);
    const rounded = spec.roundingIncrement
        ? applyRoundingIncrement(value, spec.roundingIncrement)
        : value;
    return Intl.NumberFormat(undefined, {
        maximumFractionDigits: spec.maxFractionDigits,
        minimumFractionDigits: 0,
    }).format(rounded);
}

export function formatDateTimeSeconds(valueSeconds: number): string {
    if (!Number.isFinite(valueSeconds)) return '—';
    const ms = valueSeconds * 1000;
    const d = new Date(ms);
    const hasTime =
        d.getUTCHours() !== 0 || d.getUTCMinutes() !== 0 || d.getUTCSeconds() !== 0;
    const opts: Intl.DateTimeFormatOptions = hasTime
        ? {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              hour12: false,
              timeZone: 'UTC',
          }
        : {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              timeZone: 'UTC',
          };
    return new Intl.DateTimeFormat(undefined, opts).format(d);
}

export function formatWholeNumber(value: number): string {
    if (!Number.isFinite(value)) return '—';
    return Intl.NumberFormat(undefined, {
        maximumFractionDigits: 0,
    }).format(value);
}

export function formatCurrency(value: number): string {
    if (!Number.isFinite(value)) return '—';
    return Intl.NumberFormat(undefined, {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0,
    }).format(value);
}

export function formatPercentFromRatio(value: number | null): string {
    if (value === null || !Number.isFinite(value)) return '—';
    return Intl.NumberFormat(undefined, {
        style: 'percent',
        maximumFractionDigits: 1,
    }).format(value);
}

export function truncateLabel(label: string, maxLength = 12): string {
    if (label.length <= maxLength) return label;
    return label.slice(0, maxLength) + '\u2026';
}
