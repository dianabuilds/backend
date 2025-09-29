import React from 'react';
import { Button, Drawer, Input, Switch } from '@ui';
import type { ProviderFormState } from '../types';

type ProviderDrawerProps = {
  open: boolean;
  provider: ProviderFormState | null;
  saving: boolean;
  hasAccess: boolean;
  onClose: () => void;
  onSubmit: (form: ProviderFormState) => void | Promise<void>;
};

export function ProviderDrawer({ open, provider, saving, hasAccess, onClose, onSubmit }: ProviderDrawerProps) {
  const [internal, setInternal] = React.useState<ProviderFormState | null>(provider);

  React.useEffect(() => {
    if (open) {
      setInternal(provider);
    } else {
      setInternal(null);
    }
  }, [open, provider]);

  const handleSubmit = async () => {
    if (!internal || !internal.slug.trim()) return;
    await onSubmit({
      ...internal,
      slug: internal.slug.trim(),
      title: internal.title?.trim() || undefined,
      base_url: internal.base_url?.trim() || undefined,
      api_key: internal.api_key?.trim() || undefined,
    });
  };

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={internal?.originalSlug ? 'Настройка провайдера' : 'Новый провайдер'}
      widthClass='w-[560px]'
      footer={
        hasAccess && internal ? (
          <div className='flex items-center justify-between'>
            <div className='text-xs text-gray-500'>Помните, что изменения применяются немедленно.</div>
            <Button size='sm' onClick={handleSubmit} disabled={saving || !internal.slug.trim()}>
              {saving ? 'Сохраняем...' : 'Сохранить'}
            </Button>
          </div>
        ) : null
      }
    >
      {hasAccess && internal ? (
        <div className='space-y-4 p-6'>
          <div>
            <div className='text-xs font-medium text-gray-500'>Slug</div>
            <Input
              placeholder='openai'
              value={internal.slug}
              disabled={!!internal.originalSlug}
              onChange={(e) => setInternal((prev) => (prev ? { ...prev, slug: e.target.value } : prev))}
            />
          </div>
          <div>
            <div className='text-xs font-medium text-gray-500'>Отображаемое название</div>
            <Input
              placeholder='OpenAI'
              value={internal.title || ''}
              onChange={(e) => setInternal((prev) => (prev ? { ...prev, title: e.target.value } : prev))}
            />
          </div>
          <div>
            <div className='text-xs font-medium text-gray-500'>Endpoint URL</div>
            <Input
              placeholder='https://api.openai.com/v1'
              value={internal.base_url || ''}
              onChange={(e) => setInternal((prev) => (prev ? { ...prev, base_url: e.target.value } : prev))}
            />
          </div>
          <div className='grid gap-4 md:grid-cols-2'>
            <div>
              <div className='text-xs font-medium text-gray-500'>Timeout, сек</div>
              <Input
                type='number'
                value={internal.timeout_sec ?? ''}
                onChange={(e) =>
                  setInternal((prev) =>
                    prev
                      ? {
                          ...prev,
                          timeout_sec: parseNumber(e.target.value, prev.timeout_sec ?? null),
                        }
                      : prev,
                  )
                }
              />
            </div>
            <div>
              <div className='text-xs font-medium text-gray-500'>Retries</div>
              <Input
                type='number'
                value={internal.retries ?? ''}
                onChange={(e) =>
                  setInternal((prev) =>
                    prev
                      ? {
                          ...prev,
                          retries: parseNumber(e.target.value, prev.retries ?? null),
                        }
                      : prev,
                  )
                }
              />
            </div>
          </div>
          <div className='space-y-2'>
            <label className='flex items-center gap-2 text-sm'>
              <Switch
                checked={internal.enabled}
                onChange={() => setInternal((prev) => (prev ? { ...prev, enabled: !prev.enabled } : prev))}
              />
              Провайдер активен
            </label>
            <div className='rounded-md border border-dashed border-gray-200 bg-gray-50 p-3 text-xs text-gray-600'>
              API ключ не отображается после сохранения. Чтобы обновить ключ, вставьте новое значение — старое перезапишется.
            </div>
            <Input
              placeholder='API ключ'
              value={internal.api_key || ''}
              onChange={(e) => setInternal((prev) => (prev ? { ...prev, api_key: e.target.value } : prev))}
            />
          </div>
        </div>
      ) : (
        <div className='p-6 text-sm text-gray-500'>У вас нет доступа для редактирования провайдеров.</div>
      )}
    </Drawer>
  );
}

function parseNumber(value: string, fallback: number | null) {
  if (value === '') return null;
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return fallback;
  return numeric;
}
