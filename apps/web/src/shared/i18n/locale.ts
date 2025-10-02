let currentLocale: 'en' | 'ru' = 'ru';

export type Locale = 'en' | 'ru';

export function setLocale(locale: Locale) {
  currentLocale = locale;
}

export function getLocale(): Locale {
  return currentLocale;
}

export function translate(map: Record<Locale, string>): string {
  return map[currentLocale] ?? map.ru ?? map.en;
}

export function translateWithVars(
  map: Record<Locale, string>,
  vars: Record<string, string | number>,
): string {
  const template = translate(map);
  return template.replace(/{{\s*(\w+)\s*}}/g, (_, key: string) => {
    const value = vars[key];
    return value == null ? '' : String(value);
  });
}
