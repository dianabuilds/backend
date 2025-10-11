import type { Locale } from '@shared/i18n/locale';
import { buildCanonicalUrl, isAbsoluteUrl } from './site';

type UnknownRecord = Record<string, unknown>;

type LocaleLike = Locale | string;

const FALLBACK_LOCALE_MAP: Record<Locale, Locale> = {
  en: 'ru',
  ru: 'en',
};

function toRecord(value: unknown): UnknownRecord | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null;
  }
  return value as UnknownRecord;
}

function readString(value: unknown): string | undefined {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed.length ? trimmed : undefined;
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return String(value);
  }
  return undefined;
}

function camelToSnake(value: string): string {
  return value
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/[\s-]+/g, '_')
    .toLowerCase();
}

function capitalize(value: string): string {
  if (!value) return value;
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function unique<T>(values: Iterable<T>): T[] {
  const seen = new Set<T>();
  for (const value of values) {
    if (value == null || seen.has(value)) continue;
    seen.add(value);
  }
  return Array.from(seen);
}

function candidateKeys(base: string, locale: LocaleLike): string[] {
  const normalized = String(locale).trim();
  if (!normalized) return [];
  const lower = normalized.toLowerCase();
  const upper = normalized.toUpperCase();
  const capitalized = capitalize(lower);
  return unique([
    `${base}_${lower}`,
    `${base}-${lower}`,
    `${lower}_${base}`,
    `${lower}-${base}`,
    `${base}${upper}`,
    `${base}${capitalized}`,
  ]);
}

export function pickString(source: UnknownRecord | null | undefined, ...keys: string[]): string | undefined {
  if (!source) return undefined;
  for (const key of keys) {
    const direct = readString(source[key]);
    if (direct) {
      return direct;
    }
    const nested = toRecord(source[key]);
    if (nested) {
      const nestedValue =
        readString(nested.href) ??
        readString(nested.url) ??
        readString(nested.src) ??
        readString(nested.content) ??
        readString(nested.value);
      if (nestedValue) {
        return nestedValue;
      }
    }
  }
  return undefined;
}

export function pickLocalizedString(
  source: UnknownRecord | null | undefined,
  key: string,
  locale: Locale,
  fallbackLocale?: Locale,
): string | undefined {
  if (!source) return undefined;
  const fallbacks = unique<Locale | 'default'>([
    locale,
    fallbackLocale ?? FALLBACK_LOCALE_MAP[locale],
    'default',
  ]);

  for (const currentLocale of fallbacks) {
    if (!currentLocale) continue;
    const directCandidates = candidateKeys(key, currentLocale);
    for (const candidate of directCandidates) {
      const value = readString(source[candidate]);
      if (value) {
        return value;
      }
    }

    const bucket = toRecord(source[key]);
    if (bucket) {
      const nestedValue = pickString(bucket, String(currentLocale), String(currentLocale).toLowerCase(), String(currentLocale).toUpperCase());
      if (nestedValue) {
        return nestedValue;
      }
    }

    const localeBucket =
      toRecord(source[String(currentLocale)]) ??
      toRecord(source[String(currentLocale).toLowerCase()]) ??
      toRecord(source[String(currentLocale).toUpperCase()]);
    if (localeBucket) {
      const nested = pickString(localeBucket, key, key.toLowerCase(), key.toUpperCase(), camelToSnake(key));
      if (nested) {
        return nested;
      }
    }
  }

  const direct = readString(source[key]);
  if (direct) {
    return direct;
  }
  return undefined;
}

export function extractAlternateLinks(
  source: UnknownRecord | null | undefined,
  origin: string,
): Array<{ hreflang: string; href: string }> {
  const root =
    toRecord(source?.alternates) ??
    toRecord(source?.alternate) ??
    toRecord(source?.hreflang);
  if (!root) {
    return [];
  }
  const result: Array<{ hreflang: string; href: string }> = [];
  for (const [lang, raw] of Object.entries(root)) {
    if (!lang || typeof lang !== 'string') continue;
    let href: string | undefined;
    if (typeof raw === 'string') {
      href = raw;
    } else {
      const record = toRecord(raw);
      if (record) {
        href =
          readString(record.href) ??
          readString(record.url) ??
          readString(record.path) ??
          readString(record.link);
      }
    }
    if (!href) continue;
    result.push({ hreflang: lang.trim(), href: buildCanonicalUrl(href, origin) });
  }
  return result;
}

export function ensureAbsoluteUrl(value: string | undefined, origin: string): string | undefined {
  if (!value) return undefined;
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  if (isAbsoluteUrl(trimmed)) {
    try {
      const url = new URL(trimmed);
      url.hash = '';
      return url.toString();
    } catch {
      return trimmed;
    }
  }
  return buildCanonicalUrl(trimmed, origin);
}

export type { UnknownRecord };
