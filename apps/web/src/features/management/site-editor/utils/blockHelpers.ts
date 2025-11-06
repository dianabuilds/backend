import { SCOPE_LABELS } from '../components/SiteBlockLibraryPage.constants';

export function parseStringList(value: string): string[] {
  const tokens = value
    .split(/\r?\n|,/)
    .map((token) => token.trim())
    .filter(Boolean);
  const unique: string[] = [];
  for (const token of tokens) {
    if (!unique.includes(token)) {
      unique.push(token);
    }
  }
  return unique;
}

export function normalizeStringArray(values: string[]): string[] {
  return values
    .map((value) => value.trim())
    .filter((value, index, self) => value.length > 0 && self.indexOf(value) === index);
}

export function sortStrings(values: string[]): string[] {
  return [...values].sort((a, b) => a.localeCompare(b, 'ru'));
}

export function formatScope(scope: string | null | undefined): string {
  return SCOPE_LABELS[scope ?? 'unknown'] ?? scope ?? '—';
}
