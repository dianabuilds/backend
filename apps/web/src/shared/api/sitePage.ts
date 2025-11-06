import {
  normalizeSitePageResponse,
  type SitePageBlock,
  type SitePageBlockItem,
  type SitePageFallbackEntry,
  type SitePageResponse,
} from '@caves/site-shared/site-page';
import { apiGetWithResponse } from './client';

const DEFAULT_SLUG = 'main';

export type SitePageDocument = SitePageResponse & {
  etag: string | null;
};

export function normalizeSitePage(
  payload: unknown,
  options: { fallbackSlug?: string } = {},
): SitePageResponse {
  return normalizeSitePageResponse(payload, {
    fallbackSlug: options.fallbackSlug ?? DEFAULT_SLUG,
  });
}

export async function fetchSitePage(
  slug?: string,
): Promise<{ data: SitePageDocument | null; status: number; error?: string; etag: string | null }> {
  const trimmedSlug = typeof slug === 'string' ? slug.trim() : '';
  const effectiveSlug = trimmedSlug.length ? trimmedSlug : undefined;
  const query =
    effectiveSlug && effectiveSlug !== DEFAULT_SLUG ? `?slug=${encodeURIComponent(effectiveSlug)}` : '';
  const endpoint = `/v1/public/site-page${query}`;

  try {
    const { data, response } = await apiGetWithResponse<unknown>(endpoint, { omitCredentials: true });
    const etag = response.headers.get('ETag') ?? response.headers.get('etag');
    const normalized = normalizeSitePage(data, { fallbackSlug: DEFAULT_SLUG });
    const document: SitePageDocument = {
      ...normalized,
      etag: etag ?? null,
    };
    return { data: document, status: response.status, etag: document.etag };
  } catch (error: any) {
    const status = typeof error?.status === 'number' ? error.status : 500;
    return {
      data: null,
      status,
      error: error?.message || 'Failed to load site page',
      etag: null,
    };
  }
}

export {
  normalizeSitePageResponse,
  type SitePageBlock,
  type SitePageBlockItem,
  type SitePageFallbackEntry,
  type SitePageResponse,
};
