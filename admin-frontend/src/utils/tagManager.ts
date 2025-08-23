const catalog: Set<string> = new Set();

export function normalizeTag(tag: string): string {
  return tag.trim().toLowerCase();
}

export function mergeTags(tags: string[]): string[] {
  const merged: string[] = [];
  for (const t of tags) {
    const norm = normalizeTag(t);
    if (!catalog.has(norm)) {
      catalog.add(norm);
    }
    if (!merged.includes(norm)) {
      merged.push(norm);
    }
  }
  return merged;
}

export function addToCatalog(tags: string[]) {
  for (const t of tags) {
    catalog.add(normalizeTag(t));
  }
}

export function getSuggestions(prefix: string): string[] {
  if (!prefix) return Array.from(catalog);
  const norm = normalizeTag(prefix);
  return Array.from(catalog).filter((t) => t.startsWith(norm) && t !== norm);
}

export function getCatalog(): string[] {
  return Array.from(catalog);
}
