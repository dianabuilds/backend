import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

import { OpenAPI } from '../openapi';

// Configure the generated OpenAPI client to behave like our accountApi:
// - send credentials (cookies) for CSRF/session flows
// - attach Bearer token from cookies/session
// - attach X-CSRF-Token header for mutating cross‑origin requests
function configureOpenAPI() {
  // Resolve backend base URL similar to accountApi
  const resolveBase = (): string => {
    try {
      const envBase = (import.meta.env?.VITE_API_BASE as string | undefined) || undefined;
      if (envBase) return String(envBase).replace(/\/+$/, '');
    } catch {
      /* ignore */
    }
    try {
      const loc = window.location;
      const port = String(loc.port || '');
      const isViteDev = /^517[3-6]$/.test(port);
      if (isViteDev) return `http://${loc.hostname}:8000`;
      return ''; // relative in prod/same‑origin
    } catch {
      return '';
    }
  };

  const getCookie = (name: string): string => {
    const m = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]+)`));
    return m ? decodeURIComponent(m[1]) : '';
  };

  const getAccessToken = (): string => getCookie('access_token');
  const getCsrfToken = (): string => {
    // try common names
    return (
      getCookie('XSRF-TOKEN') ||
      getCookie('xsrf-token') ||
      getCookie('csrf_token') ||
      getCookie('csrftoken') ||
      getCookie('CSRF-TOKEN')
    );
  };

  OpenAPI.BASE = resolveBase();
  OpenAPI.WITH_CREDENTIALS = true;
  OpenAPI.CREDENTIALS = 'include';
  OpenAPI.TOKEN = async () => getAccessToken();
  OpenAPI.HEADERS = async (opts) => {
    const method = String(opts.method || 'GET').toUpperCase();
    const isAuthCall = opts.url.startsWith('/auth/');
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (!isAuthCall && method !== 'GET' && method !== 'HEAD') {
      const csrf = getCsrfToken();
      if (csrf) headers['X-CSRF-Token'] = csrf;
    }
    return headers;
  };
}

const queryClient = new QueryClient();

export function AppProviders({ children }: { children: ReactNode }) {
  // one‑time OpenAPI setup on provider mount
  configureOpenAPI();
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
