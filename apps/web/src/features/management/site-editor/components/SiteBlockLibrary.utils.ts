import type { SiteBlock } from '@shared/types/management';
import type { FiltersState } from './SiteBlockLibrary.types';

export function normalize(text: string): string {
  return text
    .normalize('NFKC')
    .toLowerCase()
    .trim();
}

export function pickOwner(block: SiteBlock): string | null {
  const candidate = (block.meta as { owner?: unknown } | undefined)?.owner;
  if (typeof candidate === 'string' && candidate.trim()) {
    return candidate.trim();
  }
  return null;
}

export function pickDocumentationUrl(block: SiteBlock): string | null {
  const meta = block.meta as Record<string, unknown> | undefined;
  const candidate = meta?.documentation ?? meta?.documentation_url ?? meta?.docs;
  if (typeof candidate === 'string' && candidate.trim()) {
    return candidate.trim();
  }
  return null;
}

export function collectLocales(block: SiteBlock): string[] {
  const locales = new Set<string>();
  if (typeof block.locale === 'string' && block.locale.trim()) {
    locales.add(block.locale.trim());
  }
  if (typeof block.default_locale === 'string' && block.default_locale.trim()) {
    locales.add(block.default_locale.trim());
  }
  if (Array.isArray(block.available_locales)) {
    block.available_locales
      .filter((value): value is string => typeof value === 'string' && value.trim().length > 0)
      .forEach((value) => locales.add(value.trim()));
  }
  return Array.from(locales);
}

export function filterBlocks(blocks: SiteBlock[], filters: FiltersState): SiteBlock[] {
  const search = normalize(filters.search);
  return blocks.filter((block) => {
    if (filters.status !== 'all' && block.status !== filters.status) {
      return false;
    }
    const scope = block.scope ?? 'unknown';
    if (filters.scope !== 'all' && scope !== filters.scope) {
      return false;
    }
    if (filters.requiresPublisher === 'true' && !block.requires_publisher) {
      return false;
    }
    if (filters.requiresPublisher === 'false' && block.requires_publisher) {
      return false;
    }
    if (filters.reviewStatus !== 'all' && block.review_status !== filters.reviewStatus) {
      return false;
    }
    if (filters.locale !== 'all') {
      const locales = collectLocales(block);
      if (!locales.some((locale) => locale === filters.locale)) {
        return false;
      }
    }
    if (filters.owner !== 'all' && pickOwner(block) !== filters.owner) {
      return false;
    }
    if (search.length > 0) {
      const haystack = [
        block.title,
        block.key,
        block.section,
        pickOwner(block) ?? '',
        block.scope ?? '',
        block.comment ?? '',
        ...collectLocales(block),
      ]
        .map((value) => normalize(String(value ?? '')))
        .join(' ');
      if (!haystack.includes(search)) {
        return false;
      }
    }
    return true;
  });
}

export function isSameStringList(left: string[], right: string[]): boolean {
  if (left.length !== right.length) {
    return false;
  }
  return left.every((value, index) => value === right[index]);
}

export function joinList(values: string[]): string {
  return values.join('\\n');
}
