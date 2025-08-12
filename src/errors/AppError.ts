export type AppErrorCode =
  | 'network'
  | 'timeout'
  | 'unauthorized'
  | 'forbidden'
  | 'not_found'
  | 'conflict'
  | 'rate_limited'
  | 'server'
  | 'validation'
  | 'unknown';

export interface AppError extends Error {
  name: 'AppError';
  code: AppErrorCode;
  status?: number;
  details?: unknown;
  cause?: unknown;
}

export function createAppError(
  code: AppErrorCode,
  message: string,
  options?: { status?: number; details?: unknown; cause?: unknown }
): AppError {
  const err = new Error(message) as AppError;
  err.name = 'AppError';
  err.code = code;
  if (options?.status !== undefined) err.status = options.status;
  if (options?.details !== undefined) err.details = options.details;
  if (options?.cause !== undefined) err.cause = options.cause;
  return err;
}

export function isAppError(e: unknown): e is AppError {
  return Boolean(e) && typeof e === 'object' && (e as any).name === 'AppError' && typeof (e as any).code === 'string';
}

export function codeFromStatus(status?: number): AppErrorCode {
  if (!status) return 'unknown';
  if (status === 401) return 'unauthorized';
  if (status === 403) return 'forbidden';
  if (status === 404) return 'not_found';
  if (status === 409) return 'conflict';
  if (status === 429) return 'rate_limited';
  if (status >= 500 && status <= 599) return 'server';
  return 'unknown';
}

export function normalizeError(input: unknown): AppError {
  if (isAppError(input)) return input;

  // DOMException for AbortError (timeout/cancel)
  if (input && typeof input === 'object' && (input as any).name === 'AbortError') {
    return createAppError('timeout', 'Запрос прерван по таймауту или отменён', { cause: input });
  }

  // Fetch network error commonly throws TypeError
  if (input instanceof TypeError) {
    return createAppError('network', input.message || 'Сетевая ошибка', { cause: input });
  }

  // HTTP Response-like to AppError (if кто-то пробросил Response)
  if (input && typeof input === 'object' && 'status' in (input as any) && 'statusText' in (input as any)) {
    const resp = input as any as { status: number; statusText: string };
    return createAppError(codeFromStatus(resp.status), resp.statusText || 'HTTP ошибка', {
      status: resp.status,
      cause: input,
    });
  }

  // Generic Error
  if (input instanceof Error) {
    return createAppError('unknown', input.message || 'Неизвестная ошибка', { cause: input });
  }

  // Fallback
  return createAppError('unknown', 'Неизвестная ошибка', { details: input });
}

export function userMessageFor(error: AppError): string {
  switch (error.code) {
    case 'timeout':
      return 'Не удалось дождаться ответа. Попробуйте ещё раз.';
    case 'network':
      return 'Проблемы с сетью. Проверьте подключение и повторите попытку.';
    case 'unauthorized':
      return 'Требуется войти в систему.';
    case 'forbidden':
      return 'У вас нет прав на это действие.';
    case 'not_found':
      return 'Ресурс не найден.';
    case 'conflict':
      return 'Конфликт данных. Обновите страницу и попробуйте снова.';
    case 'rate_limited':
      return 'Слишком много запросов. Попробуйте позже.';
    case 'server':
      return 'Проблема на стороне сервера. Повторите попытку позже.';
    case 'validation':
      return 'Проверьте корректность введённых данных.';
    default:
      return 'Что-то пошло не так. Попробуйте снова.';
  }
}
