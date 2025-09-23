import { apiFetch } from './client';

export type User = {
  id: string;
  username: string;
  email?: string;
  display_name?: string;
  is_active: boolean;
  roles?: string[];
};

export async function login(login: string, password: string): Promise<User> {
  return apiFetch<User>('/auth/login', {
    method: 'POST',
    json: { login, password },
  });
}

export async function register(username: string, password: string, email?: string, display_name?: string): Promise<User> {
  return apiFetch<User>('/auth/register', {
    method: 'POST',
    json: { username, password, email, display_name },
  });
}

export async function me(): Promise<User> {
  return apiFetch<User>('/auth/me');
}

export async function refresh(): Promise<User> {
  return apiFetch<User>('/auth/refresh', { method: 'POST' });
}

export async function logout(): Promise<{ ok: boolean }>{
  return apiFetch<{ ok: boolean }>('/auth/logout', { method: 'POST' });
}

