import { beforeEach, afterEach, describe, expect, it } from 'vitest';
import {
  formatBoolean,
  formatBytes,
  formatDateTime,
  formatDuration,
  formatNumber,
  formatPercent,
  formatRelativeTime,
  truncate,
} from './format';

describe('formatDateTime', () => {
  it('formats date with minutes', () => {
    expect(formatDateTime(new Date(2025, 9, 7, 12, 34, 56))).toBe('2025-10-07 12:34');
  });

  it('respects seconds flag', () => {
    expect(formatDateTime(new Date(2025, 9, 7, 12, 34, 56), { withSeconds: true })).toBe('2025-10-07 12:34:56');
  });

  it('returns default fallback on invalid date', () => {
    expect(formatDateTime(undefined)).toBe('--');
  });

  it('supports custom fallback', () => {
    expect(formatDateTime('invalid', { fallback: 'n/a' })).toBe('n/a');
  });

  it('supports date-only mode', () => {
    expect(formatDateTime(new Date(2025, 9, 7, 12, 34, 56), { mode: 'date' })).toBe('2025-10-07');
  });

  it('supports time-only mode with seconds', () => {
    expect(formatDateTime(new Date(2025, 9, 7, 12, 34, 56), { mode: 'time', withSeconds: true })).toBe('12:34:56');
  });
});

describe('formatRelativeTime', () => {
  const base = new Date('2025-10-07T12:00:00Z');
  let originalRtf: typeof Intl.RelativeTimeFormat | undefined;

  beforeEach(() => {
    originalRtf = (Intl as any).RelativeTimeFormat;
  });

  afterEach(() => {
    if (originalRtf) {
      (Intl as any).RelativeTimeFormat = originalRtf;
    } else {
      delete (Intl as any).RelativeTimeFormat;
    }
  });

  it('falls back to short strings when Intl.RelativeTimeFormat is unavailable', () => {
    delete (Intl as any).RelativeTimeFormat;
    expect(formatRelativeTime(new Date(base.getTime() - 5 * 60 * 1000), { now: base })).toBe('5m ago');
    expect(formatRelativeTime(new Date(base.getTime() + 2 * 60 * 60 * 1000), { now: base })).toBe('in 2h');
  });

  it('uses Intl.RelativeTimeFormat when available', () => {
    class FakeRelativeTimeFormat {
      format(value: number, unit: Intl.RelativeTimeFormatUnit) {
        return `${value}-${unit}`;
      }
    }
    (Intl as any).RelativeTimeFormat = FakeRelativeTimeFormat;
    expect(formatRelativeTime(new Date(base.getTime() + 3 * 24 * 60 * 60 * 1000), { now: base })).toBe('3-day');
  });

  it('falls back to date when difference is larger than several weeks', () => {
    delete (Intl as any).RelativeTimeFormat;
    const farFuture = new Date(base.getTime() + 40 * 24 * 60 * 60 * 1000);
    expect(formatRelativeTime(farFuture, { now: base })).toBe('2025-11-16');
  });
});

describe('formatBoolean', () => {
  it('uses defaults', () => {
    expect(formatBoolean(true)).toBe('Yes');
    expect(formatBoolean(false)).toBe('No');
  });

  it('accepts custom labels', () => {
    expect(formatBoolean(true, { yes: 'Y', no: 'N' })).toBe('Y');
  });
});

describe('truncate', () => {
  it('returns original when shorter than max', () => {
    expect(truncate('hello', 10)).toBe('hello');
  });

  it('adds ellipsis when longer', () => {
    expect(truncate('abcdefghij', 7)).toBe('abcd...');
  });
});

describe('formatNumber', () => {
  it('formats numeric value', () => {
    expect(formatNumber(12345.678, { locale: 'en-US', maximumFractionDigits: 1 })).toBe('12,345.7');
  });

  it('supports compact notation', () => {
    expect(formatNumber(12500, { locale: 'en-US', compact: true, maximumFractionDigits: 1 })).toBe('12.5K');
  });

  it('returns fallback for invalid input', () => {
    expect(formatNumber(undefined)).toBe('--');
  });
});

describe('formatPercent', () => {
  it('formats fraction as percent', () => {
    expect(formatPercent(0.1234, { locale: 'en-US', maximumFractionDigits: 1 })).toBe('12.3%');
  });

  it('accepts integer percentage', () => {
    expect(formatPercent(12.34, { locale: 'en-US', isFraction: false, maximumFractionDigits: 0 })).toBe('12%');
  });
});

describe('formatBytes', () => {
  it('formats bytes with units', () => {
    expect(formatBytes(1536, { locale: 'en-US', precision: 1 })).toBe('1.5 KB');
  });

  it('handles zero', () => {
    expect(formatBytes(0)).toBe('0 B');
  });

  it('returns fallback for invalid value', () => {
    expect(formatBytes(NaN)).toBe('--');
  });
});

describe('formatDuration', () => {
  it('formats as clock when under hour', () => {
    expect(formatDuration(65)).toBe('01:05');
  });

  it('includes hours when needed', () => {
    expect(formatDuration(3725)).toBe('01:02:05');
  });

  it('supports long style', () => {
    expect(formatDuration(3725, { style: 'long' })).toBe('1h 2m 5s');
  });
});
