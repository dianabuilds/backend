export function pad2(n: number) {
  return n < 10 ? `0${n}` : String(n);
}

export function formatDateTime(input?: string | number | Date | null, opts: { withSeconds?: boolean } = {}) {
  if (!input) return '';
  const d = input instanceof Date ? input : new Date(input);
  if (Number.isNaN(d.getTime())) return '';
  const yyyy = d.getFullYear();
  const mm = pad2(d.getMonth() + 1);
  const dd = pad2(d.getDate());
  const hh = pad2(d.getHours());
  const mi = pad2(d.getMinutes());
  const ss = pad2(d.getSeconds());
  return `${yyyy}-${mm}-${dd} ${hh}:${mi}${opts.withSeconds ? `:${ss}` : ''}`;
}

export function formatBoolean(v?: any, { yes = 'Да', no = 'Нет' } = {}) {
  return v ? yes : no;
}

export function truncate(s: string, max = 80) {
  if (!s) return '';
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

export function toSlug(input: string): string {
  try {
    return String(input || '')
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .trim()
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '');
  } catch {
    return '';
  }
}
