import { describe, it, expect } from 'vitest';
import { catchErrorCodes } from './request';
import { ApiError } from './ApiError';
import type { ApiRequestOptions } from './ApiRequestOptions';
import type { ApiResult } from './ApiResult';

describe('catchErrorCodes', () => {
  const options: ApiRequestOptions = { method: 'GET', url: '/' };

  it('throws ApiError for 405 Method Not Allowed', () => {
    const result: ApiResult = {
      url: '/',
      ok: false,
      status: 405,
      statusText: 'Method Not Allowed',
      body: null,
    };

    try {
      catchErrorCodes(options, result);
      throw new Error('Expected ApiError');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).message).toBe('Method Not Allowed');
    }
  });

  it('throws ApiError for 422 Validation Error', () => {
    const result: ApiResult = {
      url: '/',
      ok: false,
      status: 422,
      statusText: 'Unprocessable Entity',
      body: null,
    };

    try {
      catchErrorCodes(options, result);
      throw new Error('Expected ApiError');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).message).toBe('Validation Error');
    }
  });
});
