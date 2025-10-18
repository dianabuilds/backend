import React from 'react';

export const HOME_FALLBACK_DEFAULT_MESSAGE = 'Не удалось загрузить главную страницу';
export const HOME_FALLBACK_TITLE = 'Раздел временно недоступен';

export type HomeUnavailableProps = {
  message: string;
  onRetry?: () => void;
};

export function HomeUnavailable({ message, onRetry }: HomeUnavailableProps): React.ReactElement {
  return (
    <section className="rounded-2xl border border-amber-300 bg-amber-50 p-8 text-center text-sm text-amber-800 dark:border-amber-500/60 dark:bg-amber-900/40 dark:text-amber-100">
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">{HOME_FALLBACK_TITLE}</h2>
        <p className="mx-auto max-w-lg text-sm">{message}</p>
        <div>
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-lg bg-primary-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:bg-primary-500 dark:hover:bg-primary-400"
            onClick={onRetry}
          >
            Обновить
          </button>
        </div>
      </div>
    </section>
  );
}
