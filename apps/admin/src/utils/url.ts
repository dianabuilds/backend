/**
 * Преобразует относительный URL (например, /static/uploads/...) в абсолютный к бэкенду.
 * Учитывает VITE_API_BASE и dev-порт Vite (5173–5176 -> http://<host>:8000).
 */
export function resolveBackendUrl(u: string | null | undefined): string | null {
  if (!u) return null;
  const url = u;

  // Протокольно-относительный
  if (url.startsWith('//')) {
    try {
      return (typeof window !== 'undefined' ? window.location.protocol : 'http:') + url;
    } catch {
      return 'http:' + url;
    }
  }
  // Уже абсолютный http/https
  if (/^https?:\/\//i.test(url)) return url;

  // База API
  let base: string | undefined;
  try {
    const envBase = (import.meta as ImportMeta & { env?: Record<string, string | undefined> })?.env
      ?.VITE_API_BASE as string | undefined;
    if (envBase) base = envBase.replace(/\/+$/, '');
  } catch {
    // ignore
  }
  if (!base) {
    try {
      const loc = window.location;
      const isViteDev = /^517[3-6]$/.test(String(loc.port || ''));
      if (isViteDev) base = `${loc.protocol}//${loc.hostname}:8000`;
    } catch {
      // ignore
    }
  }

  if (url.startsWith('/')) return (base || '') + url;
  return (base || '') + '/' + url.replace(/^\.?\//, '');
}

/**
 * Достаёт URL из тела ответа/заголовка Location и нормализует его.
 * Приоритет: file.url -> url -> path -> location -> Location header.
 * Дополнительно удаляет обрамляющие кавычки и экранирование из строки.
 */
export function extractUrlFromUploadResponse(data: unknown, headers?: Headers): string | null {
  let u: string | null =
    (data &&
      typeof data === 'object' &&
      (((data as Record<string, unknown>).file as { url?: string } | undefined)?.url ||
        (data as Record<string, unknown>).url ||
        (data as Record<string, unknown>).path ||
        (data as Record<string, unknown>).location)) ??
    (typeof data === 'string' ? data : null) ??
    (headers ? headers.get('Location') : null);

  if (!u) return null;

  // Нормализуем: trim и удаление обрамляющих кавычек/экранирования
  try {
    u = String(u).trim();
    // Если строка в виде "\"/static/..\"" — снимем экранирование
    if (/^\\?["'].*\\?["']$/.test(u)) {
      // убираем один уровень backslash-экранирования
      u = u.replace(/\\"/g, '"').replace(/\\'/g, "'");
    }
    if ((u.startsWith('"') && u.endsWith('"')) || (u.startsWith("'") && u.endsWith("'"))) {
      u = u.slice(1, -1).trim();
    }
  } catch {
    // noop
  }

  return resolveBackendUrl(u || null);
}
