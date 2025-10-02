import type { Config } from 'dompurify';
import createDOMPurify from 'dompurify';

type PurifierInstance = ReturnType<typeof createDOMPurify>;

let purifier: PurifierInstance | null = null;

function ensurePurifier(): PurifierInstance | null {
  if (purifier) return purifier;
  if (typeof window === 'undefined' || !window.document) {
    return null;
  }
  purifier = createDOMPurify(window);
  return purifier;
}

export function sanitizeHtml(html: string | null | undefined, config?: Config): string {
  if (!html) return '';
  const instance = ensurePurifier();
  if (!instance) {
    return String(html);
  }
  return instance.sanitize(html, config) as string;
}

