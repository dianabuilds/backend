import React from 'react';
import clsx from 'clsx';
import { Button, Input, Switch } from '@ui';
import type { SitePageSummary } from '@shared/types/management';
import type { UpdateSitePagePayload } from '@shared/api/management/siteEditor/types';

type SitePageInfoPanelProps = {
  page: SitePageSummary | null;
  disabled?: boolean;
  saving: boolean;
  error: string | null;
  onSubmit: (payload: UpdateSitePagePayload) => Promise<void>;
  onClearError: () => void;
};

function normalizeSlug(value: string): string {
  if (!value) {
    return '';
  }
  const sanitized = value.trim().replace(/\s+/g, '-');
  if (!sanitized) {
    return '';
  }
  return sanitized.startsWith('/') ? sanitized : `/${sanitized}`;
}

function normalizeLocale(value: string): string {
  return value.trim();
}

function normalizeTitle(value: string): string {
  return value.trim();
}

function normalizeOwner(value: string): string {
  return value.trim();
}

export function SitePageInfoPanel({
  page,
  disabled = false,
  saving,
  error,
  onSubmit,
  onClearError,
}: SitePageInfoPanelProps): React.ReactElement {
  const [title, setTitle] = React.useState('');
  const [slug, setSlug] = React.useState('');
  const [locale, setLocale] = React.useState('ru');
  const [owner, setOwner] = React.useState('');
  const [pinned, setPinned] = React.useState(false);
  const [validationError, setValidationError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!page) {
      setTitle('');
      setSlug('');
      setLocale('ru');
      setOwner('');
      setPinned(false);
      return;
    }
    setTitle(page.title ?? '');
    setSlug(normalizeSlug(page.slug ?? ''));
    setLocale(page.locale ?? 'ru');
    setOwner(page.owner ?? '');
    setPinned(Boolean(page.pinned));
    setValidationError(null);
  }, [page]);

  const initialValues = React.useMemo(() => {
    if (!page) {
      return {
        title: '',
        slug: '',
        locale: 'ru',
        owner: '',
        pinned: false,
      };
    }
    return {
      title: page.title ?? '',
      slug: normalizeSlug(page.slug ?? ''),
      locale: page.locale ?? 'ru',
      owner: page.owner ?? '',
      pinned: Boolean(page.pinned),
    };
  }, [page]);

  const handleFieldChange = React.useCallback(
    (setter: (value: string) => void) => (event: React.ChangeEvent<HTMLInputElement>) => {
      onClearError();
      setValidationError(null);
      setter(event.currentTarget.value);
    },
    [onClearError],
  );

  const handlePinnedChange = React.useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      onClearError();
      setPinned(Boolean(event.currentTarget.checked));
    },
    [onClearError],
  );

  const normalizedSlug = normalizeSlug(slug);
  const normalizedTitle = normalizeTitle(title);
  const normalizedLocale = normalizeLocale(locale);
  const normalizedOwner = normalizeOwner(owner);

  const hasChanges =
    normalizedTitle !== initialValues.title ||
    normalizedSlug !== initialValues.slug ||
    normalizedLocale !== initialValues.locale ||
    normalizedOwner !== initialValues.owner ||
    pinned !== initialValues.pinned;

  const handleReset = React.useCallback(() => {
    if (!page) {
      return;
    }
    setTitle(page.title ?? '');
    setSlug(normalizeSlug(page.slug ?? ''));
    setLocale(page.locale ?? 'ru');
    setOwner(page.owner ?? '');
    setPinned(Boolean(page.pinned));
    setValidationError(null);
    onClearError();
  }, [page, onClearError]);

  const handleBlurSlug = React.useCallback(() => {
    setSlug(normalizeSlug(slug));
  }, [slug]);

  const handleSubmit = React.useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault();
      onClearError();
      setValidationError(null);

      if (!page) {
        return;
      }
      if (!normalizedTitle) {
        setValidationError('Название не может быть пустым.');
        return;
      }
      if (!normalizedSlug) {
        setValidationError('Slug не может быть пустым.');
        return;
      }
      if (!normalizedLocale) {
        setValidationError('Локаль не может быть пустой.');
        return;
      }
      const payload: UpdateSitePagePayload = {};
      if (normalizedTitle !== initialValues.title) {
        payload.title = normalizedTitle;
      }
      if (normalizedSlug !== initialValues.slug) {
        payload.slug = normalizedSlug;
      }
      if (normalizedLocale !== initialValues.locale) {
        payload.locale = normalizedLocale;
      }
      if (normalizedOwner !== initialValues.owner) {
        payload.owner = normalizedOwner.length > 0 ? normalizedOwner : null;
      }
      if (pinned !== initialValues.pinned) {
        payload.pinned = pinned;
      }
      if (Object.keys(payload).length === 0) {
        return;
      }
      try {
        await onSubmit(payload);
      } catch {
        // Ошибка будет отображена через пропсы error
      }
    },
    [
      initialValues.locale,
      initialValues.owner,
      initialValues.pinned,
      initialValues.slug,
      initialValues.title,
      normalizedLocale,
      normalizedOwner,
      normalizedSlug,
      normalizedTitle,
      onClearError,
      onSubmit,
      page,
      pinned,
    ],
  );

  return (
    <details className="group rounded-2xl border border-gray-200/70 bg-white/95 text-gray-900 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/80 dark:text-dark-50 [&_summary::-webkit-details-marker]:hidden">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-semibold">
        <span>Основная информация</span>
        <span className="text-xs text-primary-500 group-open:hidden">Развернуть</span>
        <span className="hidden text-xs text-primary-500 group-open:block">Свернуть</span>
      </summary>
      <form className="space-y-4 border-t border-gray-100 px-4 py-4 dark:border-dark-700/60" onSubmit={handleSubmit}>
        {validationError ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-200">
            {validationError}
          </div>
        ) : null}
        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:border-rose-400/30 dark:bg-rose-400/10 dark:text-rose-200">
            {error}
          </div>
        ) : null}
        <label className="block space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200">Название</span>
          <Input
            value={title}
            onChange={handleFieldChange(setTitle)}
            disabled={disabled || saving || !page}
            placeholder="Название страницы"
          />
        </label>
        <label className="block space-y-1">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200">Slug</span>
          <Input
            value={slug}
            onChange={handleFieldChange(setSlug)}
            onBlur={handleBlurSlug}
            disabled={disabled || saving || !page}
            placeholder="/promo"
          />
        </label>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200">Локаль</span>
            <Input
              value={locale}
              onChange={handleFieldChange(setLocale)}
              disabled={disabled || saving || !page}
              placeholder="ru"
            />
          </label>
          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200">Ответственный</span>
            <Input
              value={owner}
              onChange={handleFieldChange(setOwner)}
              disabled={disabled || saving || !page}
              placeholder="marketing"
            />
          </label>
        </div>
        <div className={clsx(
          'flex items-center justify-between rounded-lg border px-3 py-2',
          pinned ? 'border-primary-200 bg-primary-50 dark:border-primary-400/30 dark:bg-primary-400/10' : 'border-gray-200 bg-white dark:border-dark-600/60 dark:bg-dark-800/80',
        )}
        >
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide text-gray-600 dark:text-dark-100">Закрепить страницу</div>
            <div className="text-[11px] text-gray-400 dark:text-dark-300">
              Закреплённые страницы отображаются в приоритетных разделах каталога.
            </div>
          </div>
          <Switch
            checked={pinned}
            onChange={handlePinnedChange}
            disabled={disabled || saving || !page}
          />
        </div>
        <div className="flex items-center justify-end gap-2">
          <Button
            type="button"
            variant="outlined"
            color="neutral"
            onClick={handleReset}
            disabled={!page || (!hasChanges && !validationError && !error) || saving || disabled}
          >
            Сбросить
          </Button>
          <Button type="submit" disabled={!page || !hasChanges || saving || disabled}>
            {saving ? 'Сохранение…' : 'Сохранить изменения'}
          </Button>
        </div>
      </form>
    </details>
  );
}

export default SitePageInfoPanel;
