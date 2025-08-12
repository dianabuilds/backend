import type { AppError } from '../errors/AppError';

type Context = Record<string, unknown>;

let userContext: { id?: string; email?: string; [k: string]: unknown } = {};

export function setUser(user: { id?: string; email?: string; [k: string]: unknown }) {
  userContext = { ...user };
}

export function addBreadcrumb(message: string, data?: Context) {
  if (import.meta.env?.DEV) {
    // eslint-disable-next-line no-console
    console.debug('[breadcrumb]', message, data);
  }
}

export function logError(error: AppError | Error | unknown, context?: Context) {
  // Здесь позже можно подключить Sentry/LogRocket/New Relic и т.д.
  if (import.meta.env?.DEV) {
    // eslint-disable-next-line no-console
    console.error('[error]', { error, context, user: userContext });
  }
  // no-op для продакшена по умолчанию
}
