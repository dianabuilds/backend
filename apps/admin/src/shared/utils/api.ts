export function ensureArray<T = unknown>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>;
    const items = obj.items as unknown;
    const dat = obj.data as unknown;
    if (Array.isArray(items)) return items as T[];
    if (Array.isArray(dat)) return dat as T[];
  }
  return [];
}

export function withQueryParams(url: string, params: Record<string, unknown | undefined>): string {
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join('&');
  if (!qs) return url;
  return `${url}${url.includes('?') ? '&' : '?'}${qs}`;
}
