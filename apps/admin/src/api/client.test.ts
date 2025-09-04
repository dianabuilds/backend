import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError } from './client';

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
  window.sessionStorage.clear();
});

describe('request', () => {
  it('returns friendly message for 405', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response('{}', { status: 405, statusText: 'Method Not Allowed', headers: { 'Content-Type': 'application/json' } }),
    );

    try {
      await api.request('/test');
      throw new Error('Expected ApiError');
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).message).toBe('Метод не поддерживается');
      expect((e as ApiError).status).toBe(405);
    }
  });

  it('returns friendly message for 422', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response('{}', { status: 422, statusText: 'Unprocessable Entity', headers: { 'Content-Type': 'application/json' } }),
    );

    try {
      await api.request('/test', { method: 'POST', json: {} });
      throw new Error('Expected ApiError');
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).message).toBe('Ошибка валидации');
      expect((e as ApiError).status).toBe(422);
    }
  });

  it('returns friendly message for 500', async () => {
    vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response('{}', { status: 500, statusText: 'Internal Server Error', headers: { 'Content-Type': 'application/json' } }),
    );

    try {
      await api.request('/test');
      throw new Error('Expected ApiError');
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).message).toBe('Внутренняя ошибка сервера');
      expect((e as ApiError).status).toBe(500);
    }
  });
});
