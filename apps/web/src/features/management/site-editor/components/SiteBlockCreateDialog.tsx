import React from 'react';
import { Button, Dialog, Input, Select, Textarea } from '@ui';
import type { CreateSiteBlockPayload } from '@shared/api/management/siteEditor/types';
import { BLOCK_SCOPE_OPTIONS } from './SiteBlockLibraryPage.constants';
import { normalizeStringArray, parseStringList, sortStrings } from '../utils/blockHelpers';
import { extractErrorMessage } from '@shared/utils/errors';

type Props = {
  open: boolean;
  onClose: () => void;
  onSubmit: (payload: CreateSiteBlockPayload) => Promise<void>;
};

const DEFAULT_FORM: CreateSiteBlockPayload & {
  localesText: string;
  is_template: boolean;
  origin_block_id: string | null;
} = {
  key: '',
  title: '',
  section: '',
  scope: 'shared',
  default_locale: 'ru',
  available_locales: ['ru'],
  requires_publisher: false,
  data: {},
  meta: {},
  localesText: 'ru',
  is_template: false,
  origin_block_id: null,
};

export function SiteBlockCreateDialog({ open, onClose, onSubmit }: Props) {
  const [form, setForm] = React.useState(DEFAULT_FORM);
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (open) {
      setForm(DEFAULT_FORM);
      setError(null);
    }
  }, [open]);

  const handleChange = React.useCallback(
    (field: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const value = event.target.value;
      setForm((prev) => ({
        ...prev,
        [field]: value,
      }));
    },
    [],
  );

  const handleScopeChange = React.useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value as CreateSiteBlockPayload['scope'];
    setForm((prev) => ({
      ...prev,
      scope: value,
    }));
  }, []);

  const handleRequiresPublisherChange = React.useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    setForm((prev) => ({
      ...prev,
      requires_publisher: event.target.value === 'true',
    }));
  }, []);

  const handleTemplateChange = React.useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const nextIsTemplate = event.target.value === 'template';
    setForm((prev) => ({
      ...prev,
      is_template: nextIsTemplate,
      origin_block_id: nextIsTemplate ? null : prev.origin_block_id,
    }));
  }, []);

  const handleSubmit = React.useCallback(async () => {
    if (submitting) {
      return;
    }
    const key = form.key.trim();
    const title = form.title.trim() || key;
    if (!key) {
      setError('Укажите уникальный ключ блока');
      return;
    }
    if (!title) {
      setError('Укажите название блока');
      return;
    }
    const section = form.section.trim() || 'general';
    const defaultLocale = form.default_locale?.trim() || null;
    const locales = sortStrings(
      normalizeStringArray(parseStringList(form.localesText ?? '').map((locale) => locale.toLowerCase())),
    );
    setSubmitting(true);
    setError(null);
    try {
      const payload: CreateSiteBlockPayload = {
        key,
        title,
        section,
        scope: form.scope,
        default_locale: defaultLocale,
        available_locales: locales,
        requires_publisher: form.requires_publisher,
        data: form.data,
        is_template: form.is_template,
        origin_block_id: form.is_template ? null : form.origin_block_id?.trim() || null,
      };
      if (form.meta && Object.keys(form.meta).length > 0) {
        payload.meta = form.meta;
      }
      await onSubmit(payload);
      onClose();
      setForm(DEFAULT_FORM);
    } catch (err) {
      setError(extractErrorMessage(err, 'Не удалось создать блок'));
    } finally {
      setSubmitting(false);
    }
  }, [form, onClose, onSubmit, submitting]);

  return (
    <Dialog
      open={open}
      onClose={() => {
        if (!submitting) {
          onClose();
        }
      }}
      title="Создание блока"
      footer={
        <>
          <Button variant="outlined" color="neutral" onClick={onClose} disabled={submitting}>
            Отмена
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? 'Создание…' : 'Создать'}
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <p className="text-sm text-gray-600 dark:text-dark-200">
          Укажите основные параметры блока. Более подробные метаданные можно настроить после создания.
        </p>
        <div className="grid gap-3 md:grid-cols-2">
          <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
            <span>Ключ</span>
            <Input value={form.key} onChange={handleChange('key')} placeholder="header-main" disabled={submitting} />
          </label>
          <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
            <span>Название</span>
            <Input value={form.title} onChange={handleChange('title')} placeholder="Хедер" disabled={submitting} />
          </label>
          <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
            <span>Секция</span>
            <Input value={form.section} onChange={handleChange('section')} placeholder="header" disabled={submitting} />
          </label>
          <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
            <span>Scope</span>
            <Select value={form.scope ?? 'shared'} onChange={handleScopeChange} disabled={submitting}>
              {BLOCK_SCOPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </label>
          <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
            <span>Основная локаль</span>
            <Input value={form.default_locale ?? ''} onChange={handleChange('default_locale')} placeholder="ru" disabled={submitting} />
          </label>
          <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300 md:col-span-2">
            <span>Доступные локали</span>
            <Textarea
              value={form.localesText}
              onChange={handleChange('localesText')}
              rows={2}
              placeholder="ru&#10;en"
              disabled={submitting}
            />
          </label>
          <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
            <span>Требует publisher</span>
            <Select value={form.requires_publisher ? 'true' : 'false'} onChange={handleRequiresPublisherChange} disabled={submitting}>
              <option value="false">Нет</option>
              <option value="true">Да</option>
            </Select>
          </label>
          <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
            <span>Тип блока</span>
            <Select value={form.is_template ? 'template' : 'content'} onChange={handleTemplateChange} disabled={submitting}>
              <option value="content">Контентный блок</option>
              <option value="template">Шаблон («рыба»)</option>
            </Select>
          </label>
          <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300 md:col-span-2">
            <span>ID исходного блока (опционально)</span>
            <Input
              value={form.origin_block_id ?? ''}
              onChange={handleChange('origin_block_id')}
              placeholder="UUID блока-источника"
              disabled={submitting || form.is_template}
            />
            <span className="text-[11px] font-normal normal-case text-gray-500 dark:text-dark-300">
              Оставьте пустым, чтобы создать блок с нуля. Используйте для привязки к существующему шаблону.
            </span>
          </label>
        </div>
        {error ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
            {error}
          </div>
        ) : null}
      </div>
    </Dialog>
  );
}
