const rawSupported =
  process.env.NEXT_PUBLIC_SUPPORTED_LOCALES ?? "ru,en";

export const SUPPORTED_LOCALES = rawSupported
  .split(",")
  .map((locale) => locale.trim())
  .filter((locale) => locale.length > 0);

const fallbackDefault =
  process.env.NEXT_PUBLIC_DEFAULT_LOCALE ?? SUPPORTED_LOCALES[0] ?? "ru";

export const DEFAULT_LOCALE = SUPPORTED_LOCALES.includes(fallbackDefault)
  ? fallbackDefault
  : SUPPORTED_LOCALES[0] ?? "ru";

export type Locale = (typeof SUPPORTED_LOCALES)[number];

export function isSupportedLocale(locale: string | undefined): locale is Locale {
  if (!locale) {
    return false;
  }
  return SUPPORTED_LOCALES.includes(locale);
}

export function normalizeLocale(
  locale: string | undefined,
): Locale {
  if (isSupportedLocale(locale)) {
    return locale;
  }
  return DEFAULT_LOCALE;
}
