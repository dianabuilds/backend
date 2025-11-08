import type { SiteBlock } from '@shared/types/management';

export function collectLocales(block: SiteBlock | null | undefined): string[] {
  if (!block) {
    return [];
  }
  const locales = new Set<string>();
  if (typeof block.locale === 'string' && block.locale.trim()) {
    locales.add(block.locale.trim().toLowerCase());
  }
  if (typeof block.default_locale === 'string' && block.default_locale.trim()) {
    locales.add(block.default_locale.trim().toLowerCase());
  }
  if (Array.isArray(block.available_locales)) {
    block.available_locales
      .filter((value): value is string => typeof value === 'string' && value.trim().length > 0)
      .forEach((value) => locales.add(value.trim().toLowerCase()));
  }
  return Array.from(locales);
}

export function pickDocumentationUrl(
  source: Pick<SiteBlock, 'meta'> | { documentation_url?: string | null } | null | undefined,
): string | null {
  if (!source) {
    return null;
  }
  if ('documentation_url' in source) {
    const directUrl = (source as { documentation_url?: unknown }).documentation_url;
    if (typeof directUrl === 'string' && directUrl.trim()) {
      return directUrl.trim();
    }
  }
  const meta = (source as { meta?: Record<string, unknown> }).meta;
  if (meta && typeof meta === 'object') {
    const direct = (meta as Record<string, unknown>).documentation_url;
    if (typeof direct === 'string' && direct.trim()) {
      return direct.trim();
    }
    const legacy = (meta as Record<string, unknown>).documentation;
    if (typeof legacy === 'string' && legacy.trim()) {
      return legacy.trim();
    }
    const links = (meta as Record<string, unknown>).links;
    if (links && typeof links === 'object' && !Array.isArray(links)) {
      const docLink = (links as Record<string, unknown>).documentation;
      if (typeof docLink === 'string' && docLink.trim()) {
        return docLink.trim();
      }
    }
  }
  return null;
}

export function isSameStringList(left: string[], right: string[]): boolean {
  if (left.length !== right.length) {
    return false;
  }
  return left.every((value, index) => value === right[index]);
}

export function joinList(values: string[]): string {
  return values.join('\n');
}
