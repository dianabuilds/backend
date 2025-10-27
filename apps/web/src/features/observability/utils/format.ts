import { formatDateTime, formatNumber as baseFormatNumber, formatPercent as baseFormatPercent } from '@shared/utils/format';

const FALLBACK = '—';
const EN_LOCALE = 'en-US';

export function formatNumber(value: number | string | null | undefined, options?: { minimumFractionDigits?: number }) {
  return baseFormatNumber(value, {
    locale: EN_LOCALE,
    maximumFractionDigits: options?.minimumFractionDigits ?? 0,
    minimumFractionDigits: options?.minimumFractionDigits,
    defaultValue: FALLBACK,
  });
}

export function formatPercent(
  value: number | string | null | undefined,
  options?: { maximumFractionDigits?: number; isFraction?: boolean },
) {
  return baseFormatPercent(value, {
    locale: EN_LOCALE,
    maximumFractionDigits: options?.maximumFractionDigits ?? 1,
    isFraction: options?.isFraction ?? true,
    defaultValue: FALLBACK,
  });
}

export function formatMs(value: number | null | undefined, unit = 'ms') {
  if (typeof value !== 'number' || !Number.isFinite(value)) return FALLBACK;
  return `${Math.round(value)} ${unit}`;
}

export const formatLatency = formatMs;

export function formatCurrency(value: number | null | undefined, currency: string) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return FALLBACK;
  return new Intl.NumberFormat(EN_LOCALE, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  }).format(value);
}

export function formatUpdated(date: Date | null | undefined) {
  if (!date) return FALLBACK;
  return formatDateTime(date, {
    locale: EN_LOCALE,
    mode: 'time',
    withSeconds: true,
    fallback: FALLBACK,
  });
}
