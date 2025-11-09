import { apiGet } from '../../client';
import { ensureArray, isObjectRecord, pickNullableString, pickString } from '../utils';

import type {
  FetchOptions,
  SiteComponentCatalogResponse,
  SiteComponentSchemaResponse,
  SiteComponentSummary,
} from './types';

function normalizeComponentSummary(value: unknown): SiteComponentSummary | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const key = pickString(value.key);
  const title = pickString(value.title);
  const section = pickString(value.section);
  if (!key || !title || !section) {
    return null;
  }
  const locales = ensureArray(value.locales, (entry): string | null => {
    if (typeof entry !== 'string') {
      return null;
    }
    const normalized = entry.trim();
    return normalized || null;
  }).filter((entry): entry is string => typeof entry === 'string' && entry.length > 0);
  const version = pickString(value.version) ?? '0';
  const schemaUrl = pickString(value.schema_url);
  if (!schemaUrl) {
    return null;
  }
  return {
    key,
    title,
    section,
    description: pickNullableString(value.description),
    version,
    locales,
    thumbnail_url: pickNullableString(value.thumbnail_url) ?? undefined,
    schema_url: schemaUrl,
  };
}

export async function fetchComponentCatalog(
  options: FetchOptions = {},
): Promise<SiteComponentCatalogResponse> {
  const response = await apiGet<Record<string, unknown>>('/v1/site/components', options);
  const items = ensureArray(response?.items, normalizeComponentSummary).filter(
    (entry): entry is SiteComponentSummary => entry != null,
  );
  return { items };
}

export async function fetchComponent(
  key: string,
  options: FetchOptions = {},
): Promise<SiteComponentSummary> {
  if (!key) {
    throw new Error('site_component_missing_key');
  }
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/components/${encodeURIComponent(key)}`,
    options,
  );
  const component = normalizeComponentSummary(response);
  if (!component) {
    throw new Error('site_component_invalid_response');
  }
  return component;
}

export async function fetchComponentSchema(
  key: string,
  options: FetchOptions = {},
): Promise<SiteComponentSchemaResponse> {
  if (!key) {
    throw new Error('site_component_missing_key');
  }
  const schema = await apiGet<Record<string, unknown>>(
    `/v1/site/components/${encodeURIComponent(key)}/schema`,
    options,
  );
  return {
    version: pickString((schema as Record<string, unknown>).version) ?? null,
    schema: isObjectRecord(schema) ? (schema as Record<string, unknown>) : {},
  };
}
