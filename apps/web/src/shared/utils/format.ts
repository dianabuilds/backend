const DEFAULT_FALLBACK = '--';

export function pad2(n: number): string {
  return n < 10 ? `0${n}` : String(n);
}

function toDate(input?: string | number | Date | null): Date | null {
  if (!input && input !== 0) return null;
  const value = input instanceof Date ? input : new Date(input);
  return Number.isNaN(value.getTime()) ? null : value;
}

export type FormatDateTimeMode = 'datetime' | 'date' | 'time';

export type FormatDateTimeOptions = {
  withSeconds?: boolean;
  fallback?: string;
  mode?: FormatDateTimeMode;
  locale?: string;
  timeZone?: string;
  hour12?: boolean;
};

export function formatDateTime(
  input?: string | number | Date | null,
  opts: FormatDateTimeOptions = {},
): string {
  const {
    withSeconds = false,
    fallback = DEFAULT_FALLBACK,
    mode = 'datetime',
    locale,
    timeZone,
    hour12,
  } = opts;

  const date = toDate(input);
  if (!date) return fallback;

  const wantsIntl = Boolean(locale || timeZone || hour12 !== undefined);

  if (wantsIntl && typeof Intl !== 'undefined' && typeof Intl.DateTimeFormat !== 'undefined') {
    const options: Intl.DateTimeFormatOptions = {
      timeZone,
      hour12,
    };

    if (mode === 'datetime' || mode === 'date') {
      options.year = 'numeric';
      options.month = '2-digit';
      options.day = '2-digit';
    }

    if (mode === 'datetime' || mode === 'time') {
      options.hour = '2-digit';
      options.minute = '2-digit';
      if (withSeconds) options.second = '2-digit';
    }

    const formatter = new Intl.DateTimeFormat(locale || undefined, options);
    return formatter.format(date);
  }

  const yyyy = date.getFullYear();
  const mm = pad2(date.getMonth() + 1);
  const dd = pad2(date.getDate());
  const hh = pad2(date.getHours());
  const mi = pad2(date.getMinutes());
  const ss = pad2(date.getSeconds());

  if (mode === 'date') {
    return `${yyyy}-${mm}-${dd}`;
  }

  const time = withSeconds ? `${hh}:${mi}:${ss}` : `${hh}:${mi}`;
  if (mode === 'time') {
    return time;
  }

  return `${yyyy}-${mm}-${dd} ${time}`;
}

export type FormatRelativeTimeOptions = {
  now?: number | Date;
  fallback?: string;
  locale?: string;
  numeric?: 'always' | 'auto';
  format?: 'long' | 'short' | 'narrow';
};

export function formatRelativeTime(
  input?: string | number | Date | null,
  { now = Date.now(), fallback = DEFAULT_FALLBACK, locale, numeric = 'auto', format = 'short' }: FormatRelativeTimeOptions = {},
): string {
  const target = toDate(input);
  if (!target) return fallback;

  const reference = now instanceof Date ? now.getTime() : now;
  const diffMs = target.getTime() - reference;
  const absMs = Math.abs(diffMs);

  const minute = 60_000;
  const hour = 60 * minute;
  const day = 24 * hour;
  const week = 7 * day;

  const makeRtf = () => {
    if (typeof Intl === 'undefined' || typeof Intl.RelativeTimeFormat === 'undefined') {
      return null;
    }
    try {
      return new Intl.RelativeTimeFormat(locale || undefined, { numeric, style: format });
    } catch {
      return null;
    }
  };

  const rtf = makeRtf();

  const formatWithIntl = (value: number, unit: Intl.RelativeTimeFormatUnit): string | null => {
    if (!rtf) return null;
    return rtf.format(value, unit);
  };

  const fallbackFormat = (value: number, unit: 'm' | 'h' | 'd' | 'w'): string => {
    const abs = Math.abs(value);
    if (value < 0) {
      return `${abs}${unit} ago`;
    }
    return `in ${abs}${unit}`;
  };

  if (absMs < minute) {
    const intl = formatWithIntl(Math.trunc(diffMs / 1000), 'second');
    if (intl) return intl;
    return diffMs <= 0 ? 'just now' : 'in a moment';
  }

  if (absMs < hour) {
    const value = Math.round(diffMs / minute);
    const intl = formatWithIntl(value, 'minute');
    return intl ?? fallbackFormat(value, 'm');
  }

  if (absMs < day) {
    const value = Math.round(diffMs / hour);
    const intl = formatWithIntl(value, 'hour');
    return intl ?? fallbackFormat(value, 'h');
  }

  if (absMs < week) {
    const value = Math.round(diffMs / day);
    const intl = formatWithIntl(value, 'day');
    return intl ?? fallbackFormat(value, 'd');
  }

  if (absMs < week * 4) {
    const value = Math.round(diffMs / week);
    const intl = formatWithIntl(value, 'week');
    return intl ?? fallbackFormat(value, 'w');
  }

  return formatDateTime(target, { fallback, locale, timeZone: undefined, mode: 'date' });
}

export function formatBoolean(value: unknown, { yes = 'Yes', no = 'No' } = {}): string {
  return value ? yes : no;
}

export function truncate(input: string, max = 80, ellipsis = '...'): string {
  if (!input) return '';
  if (input.length <= max) return input;
  if (max <= ellipsis.length) return ellipsis.slice(0, max);
  return `${input.slice(0, max - ellipsis.length)}${ellipsis}`;
}

export type FormatNumberOptions = {
  locale?: string;
  maximumFractionDigits?: number;
  minimumFractionDigits?: number;
  defaultValue?: string;
  compact?: boolean;
  signDisplay?: 'auto' | 'always' | 'never' | 'exceptZero';
};

export function formatNumber(
  value: number | string | null | undefined,
  {
    locale = 'ru-RU',
    maximumFractionDigits = 2,
    minimumFractionDigits,
    defaultValue = DEFAULT_FALLBACK,
    compact = false,
    signDisplay = 'auto',
  }: FormatNumberOptions = {},
): string {
  if (value == null) return defaultValue;
  const numeric = typeof value === 'string' ? Number(value) : value;
  if (!Number.isFinite(numeric)) return defaultValue;
  const formatter = new Intl.NumberFormat(locale, {
    maximumFractionDigits,
    ...(minimumFractionDigits != null ? { minimumFractionDigits } : {}),
    ...(compact ? { notation: 'compact', compactDisplay: 'short' } : {}),
    signDisplay,
  });
  return formatter.format(numeric);
}

export type FormatPercentOptions = {
  locale?: string;
  maximumFractionDigits?: number;
  defaultValue?: string;
  signDisplay?: 'auto' | 'always' | 'never' | 'exceptZero';
  isFraction?: boolean;
};

export function formatPercent(
  value: number | string | null | undefined,
  {
    locale = 'ru-RU',
    maximumFractionDigits = 1,
    defaultValue = DEFAULT_FALLBACK,
    signDisplay = 'auto',
    isFraction = true,
  }: FormatPercentOptions = {},
): string {
  if (value == null) return defaultValue;
  let numeric = typeof value === 'string' ? Number(value) : value;
  if (!Number.isFinite(numeric)) return defaultValue;
  if (!isFraction) {
    numeric /= 100;
  }
  const formatter = new Intl.NumberFormat(locale, {
    style: 'percent',
    maximumFractionDigits,
    signDisplay,
  });
  return formatter.format(numeric);
}

export type FormatBytesOptions = {
  precision?: number;
  defaultValue?: string;
  locale?: string;
};

const BYTE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'] as const;

export function formatBytes(
  value: number | null | undefined,
  { precision = 1, defaultValue = DEFAULT_FALLBACK, locale = 'ru-RU' }: FormatBytesOptions = {},
): string {
  if (value == null) return defaultValue;
  if (!Number.isFinite(value)) return defaultValue;
  if (value === 0) return '0 B';

  let unitIndex = 0;
  let absolute = Math.abs(value);
  while (absolute >= 1024 && unitIndex < BYTE_UNITS.length - 1) {
    absolute /= 1024;
    unitIndex += 1;
  }

  const signedValue = value < 0 ? -absolute : absolute;
  const formatter = new Intl.NumberFormat(locale, {
    maximumFractionDigits: Math.max(0, precision),
  });
  return `${formatter.format(signedValue)} ${BYTE_UNITS[unitIndex]}`;
}

export type FormatDurationOptions = {
  style?: 'clock' | 'long';
  defaultValue?: string;
};

export function formatDuration(
  value: number | null | undefined,
  { style = 'clock', defaultValue = DEFAULT_FALLBACK }: FormatDurationOptions = {},
): string {
  if (value == null || !Number.isFinite(value)) return defaultValue;
  const totalSeconds = Math.max(0, Math.floor(value));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (style === 'clock') {
    if (hours > 0) return `${pad2(hours)}:${pad2(minutes)}:${pad2(seconds)}`;
    return `${pad2(minutes)}:${pad2(seconds)}`;
  }

  const parts: string[] = [];
  if (hours) parts.push(`${hours}h`);
  if (minutes) parts.push(`${minutes}m`);
  if (!hours || seconds || parts.length === 0) parts.push(`${seconds}s`);
  return parts.join(' ');
}


