import { OpenAPI } from '../openapi';

export { apiFetch } from '../api/client';

const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env ?? {};

export const API_BASE_URL: string = env.API_BASE_URL ?? '';
export const CORS_ALLOW_CREDENTIALS: boolean = /^true$/i.test(env.CORS_ALLOW_CREDENTIALS ?? '');

OpenAPI.BASE = API_BASE_URL;
OpenAPI.WITH_CREDENTIALS = CORS_ALLOW_CREDENTIALS;
if (CORS_ALLOW_CREDENTIALS) {
  OpenAPI.CREDENTIALS = 'include';
}

/**
 * Thin wrapper around fetch that prefixes API_BASE_URL for relative paths and
 * sets credentials: "include" when CORS_ALLOW_CREDENTIALS is true.
 */
export function http(input: RequestInfo, init: RequestInit = {}): Promise<Response> {
  const url =
    typeof input === 'string' && input.startsWith('/') && API_BASE_URL
      ? API_BASE_URL.replace(/\/+$/, '') + input
      : input;

  const credentialsInit = CORS_ALLOW_CREDENTIALS ? { credentials: 'include' as const } : {};
  return fetch(url, { ...init, ...credentialsInit });
}

export default http;
