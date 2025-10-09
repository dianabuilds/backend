
import { apiFetch } from './client';

export type AuthUser = {
  id?: string;
  username?: string;
  email?: string | null;
  display_name?: string | null;
  displayName?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  avatar_url?: string | null;
  avatarUrl?: string | null;
  role?: string | null;
  roles?: string[] | null;
  is_active?: boolean;
  isActive?: boolean;
  authSource?: string | null;
  meta?: Record<string, unknown> | null;
  [key: string]: unknown;
};

export type AuthSession = {
  access_token?: string | null;
  refresh_token?: string | null;
  csrf_token?: string | null;
  expires_in?: number | null;
  token_type?: string | null;
  user?: AuthUser | null;
  auth?: {
    source?: string | null;
    [key: string]: unknown;
  } | null;
  [key: string]: unknown;
};

export type CurrentUserResponse = {
  user?: AuthUser | null;
  [key: string]: unknown;
};

export type LoginPayload = {
  login: string;
  password: string;
  remember?: boolean;
};

export type LoginOptions = {
  endpoint?: string;
  signal?: AbortSignal;
};

const DEFAULT_LOGIN_ENDPOINT = '/v1/auth/login';
const DEFAULT_LOGOUT_ENDPOINT = '/v1/auth/logout';
const DEFAULT_REFRESH_ENDPOINT = '/v1/auth/refresh';
const DEFAULT_REGISTER_ENDPOINT = '/v1/auth/register';
const DEFAULT_ME_ENDPOINT = '/v1/users/me';

function resolveEndpoint(endpoint: string | undefined, fallback: string): string {
  if (!endpoint) {
    return fallback;
  }
  return endpoint;
}

export async function login(payload: LoginPayload, options: LoginOptions = {}): Promise<AuthSession> {
  const endpoint = resolveEndpoint(options.endpoint, DEFAULT_LOGIN_ENDPOINT);
  return apiFetch<AuthSession>(endpoint, { method: 'POST', json: payload, signal: options.signal });
}

export type LogoutOptions = {
  endpoint?: string;
  signal?: AbortSignal;
};

export async function logout(options: LogoutOptions = {}): Promise<{ ok: boolean } | Record<string, unknown>> {
  const endpoint = resolveEndpoint(options.endpoint, DEFAULT_LOGOUT_ENDPOINT);
  return apiFetch(endpoint, { method: 'POST', json: {}, signal: options.signal });
}

export type RefreshOptions = {
  endpoint?: string;
  signal?: AbortSignal;
};

export async function refresh(options: RefreshOptions = {}): Promise<AuthSession> {
  const endpoint = resolveEndpoint(options.endpoint, DEFAULT_REFRESH_ENDPOINT);
  return apiFetch<AuthSession>(endpoint, { method: 'POST', signal: options.signal });
}

export type FetchCurrentUserOptions = {
  endpoint?: string;
  signal?: AbortSignal;
};

export async function fetchCurrentUser(options: FetchCurrentUserOptions = {}): Promise<CurrentUserResponse> {
  const endpoint = resolveEndpoint(options.endpoint, DEFAULT_ME_ENDPOINT);
  return apiFetch<CurrentUserResponse>(endpoint, { signal: options.signal });
}

export type RegisterPayload = {
  username: string;
  password: string;
  email?: string;
  display_name?: string;
};

export type RegisterOptions = {
  endpoint?: string;
  signal?: AbortSignal;
};

export async function register(payload: RegisterPayload, options: RegisterOptions = {}): Promise<AuthUser> {
  const endpoint = resolveEndpoint(options.endpoint, DEFAULT_REGISTER_ENDPOINT);
  return apiFetch<AuthUser>(endpoint, { method: 'POST', json: payload, signal: options.signal });
}
