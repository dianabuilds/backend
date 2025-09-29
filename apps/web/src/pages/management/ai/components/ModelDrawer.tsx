import React from 'react';
import { Button, Drawer, Input, Select, Switch } from '@ui';
import type { ModelFormState, Provider } from '../types';

type ModelDrawerProps = {
  open: boolean;
  model: ModelFormState | null;
  providers: Provider[];
  saving: boolean;
  onClose: () => void;
  onSubmit: (form: ModelFormState) => void | Promise<void>;
  onCreateProvider?: () => void;
  hasProviderAccess: boolean;
};

const MODEL_WIZARD_STEPS: Array<{ key: string; label: string; hint?: string }> = [
  { key: 'basic', label: 'Основные параметры', hint: 'Название, провайдер и статус модели' },
  { key: 'limits', label: 'Лимиты и сценарии', hint: 'Суточные/месячные ограничения и назначение модели' },
  { key: 'review', label: 'Fallback и подтверждение', hint: 'Приоритет fallback и финальная проверка' },
];

export function ModelDrawer({ open, model, providers, saving, onClose, onSubmit, onCreateProvider, hasProviderAccess }: ModelDrawerProps) {
  const [internal, setInternal] = React.useState<ModelFormState | null>(model);
  const [step, setStep] = React.useState(0);

  React.useEffect(() => {
    if (open) {
      setInternal(model);
      setStep(0);
    } else {
      setInternal(null);
    }
  }, [open, model]);

  const canProceed = !!(internal?.name?.trim() && internal?.provider_slug?.trim());
  const isLastStep = step >= MODEL_WIZARD_STEPS.length - 1;

  const handleSubmit = async () => {
    if (!internal || !canProceed) return;
    await onSubmit({
      ...internal,
      name: internal.name.trim(),
      provider_slug: internal.provider_slug.trim(),
      version: internal.version?.trim() || null,
      params: {
        ...internal.params,
        limits: {
          daily_tokens: normalizeNumber(internal.params.limits?.daily_tokens),
          monthly_tokens: normalizeNumber(internal.params.limits?.monthly_tokens),
        },
        fallback_priority: normalizeNumber(internal.params.fallback_priority),
      },
    });
  };

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={internal?.id ? 'Редактирование модели' : 'Новая модель'}
      widthClass='w-[720px]'
      footer={
        internal ? (
          <div className='flex flex-wrap items-center justify-between gap-3'>
            <div className='text-xs text-gray-500'>
              Шаг {step + 1} из {MODEL_WIZARD_STEPS.length}: {MODEL_WIZARD_STEPS[step]?.label}
            </div>
            <div className='flex items-center gap-2'>
              <Button
                size='sm'
                variant='ghost'
                color='neutral'
                onClick={() => setStep((prev) => Math.max(0, prev - 1))}
                disabled={step === 0}
              >
                Назад
              </Button>
              {isLastStep ? (
                <Button size='sm' onClick={handleSubmit} disabled={!canProceed || saving}>
                  {saving ? 'Сохраняем...' : 'Сохранить'}
                </Button>
              ) : (
                <Button size='sm' onClick={() => setStep((prev) => Math.min(MODEL_WIZARD_STEPS.length - 1, prev + 1))} disabled={!canProceed}>
                  Далее
                </Button>
              )}
            </div>
          </div>
        ) : null
      }
    >
      {internal ? (
        <div className='space-y-6 p-6'>
          <div className='flex flex-wrap items-center gap-2'>
            {MODEL_WIZARD_STEPS.map((item, index) => (
              <div
                key={item.key}
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  index === step
                    ? 'bg-primary-600 text-white'
                    : index < step
                      ? 'bg-primary-100 text-primary-700'
                      : 'bg-gray-100 text-gray-600'
                }`}
              >
                {index + 1}. {item.label}
              </div>
            ))}
          </div>

          {MODEL_WIZARD_STEPS[step]?.hint ? (
            <div className='rounded-md border border-dashed border-gray-200 bg-gray-50 p-3 text-xs text-gray-600'>
              {MODEL_WIZARD_STEPS[step]?.hint}
            </div>
          ) : null}

          {step === 0 ? (
            <div className='space-y-4'>
              <div className='grid gap-4 md:grid-cols-2'>
                <div>
                  <div className='text-xs font-medium text-gray-500'>Название модели</div>
                  <Input value={internal.name} placeholder='system-name' onChange={(e) => updateField(setInternal, 'name', e.target.value)} />
                </div>
                <div>
                  <div className='text-xs font-medium text-gray-500'>Версия (опционально)</div>
                  <Input value={internal.version || ''} placeholder='gpt-4o-mini' onChange={(e) => updateField(setInternal, 'version', e.target.value)} />
                </div>
              </div>

              <div className='grid gap-4 md:grid-cols-[2fr,1fr]'>
                <div>
                  <div className='text-xs font-medium text-gray-500'>Провайдер</div>
                  <Select
                    value={internal.provider_slug}
                    onChange={(e: any) =>
                      setInternal((prev) => (prev ? { ...prev, provider_slug: e.target.value } : prev))
                    }
                  >
                    <option value=''>Выберите провайдера</option>
                    {providers.map((provider) => (
                      <option key={provider.slug} value={provider.slug}>
                        {provider.title ? `${provider.title} (${provider.slug})` : provider.slug}
                      </option>
                    ))}
                  </Select>
                  {hasProviderAccess ? (
                    <Button size='sm' variant='ghost' color='neutral' className='mt-2' onClick={onCreateProvider}>
                      Создать нового провайдера
                    </Button>
                  ) : null}
                </div>
                <div className='flex items-center gap-3'>
                  <Switch
                    checked={(internal.status || 'active') !== 'disabled'}
                    onChange={() =>
                      setInternal((prev) =>
                        prev
                          ? {
                              ...prev,
                              status: (prev.status || 'active') === 'disabled' ? 'active' : 'disabled',
                            }
                          : prev,
                      )
                    }
                  />
                  <div className='text-sm'>Включено</div>
                </div>
              </div>

              <div className='flex items-center gap-3'>
                <Switch
                  checked={!!internal.is_default}
                  onChange={() => setInternal((prev) => (prev ? { ...prev, is_default: !prev.is_default } : prev))}
                />
                <div className='text-sm'>Использовать как primary по умолчанию</div>
              </div>
            </div>
          ) : null}

          {step === 1 ? (
            <div className='space-y-4'>
              <div className='grid gap-4 md:grid-cols-2'>
                <div>
                  <div className='text-xs font-medium text-gray-500'>Лимит токенов в день</div>
                  <Input
                    type='number'
                    placeholder='например, 100000'
                    value={internal.params.limits?.daily_tokens ?? ''}
                    onChange={(e) =>
                      setInternal((prev) =>
                        prev
                          ? {
                              ...prev,
                              params: {
                                ...prev.params,
                                limits: {
                                  ...(prev.params.limits || {}),
                                  daily_tokens: parseNumber(e.target.value, prev.params.limits?.daily_tokens ?? null),
                                },
                              },
                            }
                          : prev,
                      )
                    }
                  />
                </div>
                <div>
                  <div className='text-xs font-medium text-gray-500'>Лимит токенов в месяц</div>
                  <Input
                    type='number'
                    placeholder='например, 2000000'
                    value={internal.params.limits?.monthly_tokens ?? ''}
                    onChange={(e) =>
                      setInternal((prev) =>
                        prev
                          ? {
                              ...prev,
                              params: {
                                ...prev.params,
                                limits: {
                                  ...(prev.params.limits || {}),
                                  monthly_tokens: parseNumber(e.target.value, prev.params.limits?.monthly_tokens ?? null),
                                },
                              },
                            }
                          : prev,
                      )
                    }
                  />
                </div>
              </div>

              <div className='space-y-2'>
                <div className='text-xs font-medium text-gray-500'>Доступные сценарии</div>
                <div className='flex flex-wrap gap-4'>
                  <label className='flex items-center gap-2 text-sm'>
                    <Switch checked={!!internal.params.usage?.content} onChange={() => toggleUsage(setInternal, 'content')} />
                    Генерация контента
                  </label>
                  <label className='flex items-center gap-2 text-sm'>
                    <Switch checked={!!internal.params.usage?.quests} onChange={() => toggleUsage(setInternal, 'quests')} />
                    AI-квесты
                  </label>
                  <label className='flex items-center gap-2 text-sm'>
                    <Switch checked={!!internal.params.usage?.moderation} onChange={() => toggleUsage(setInternal, 'moderation')} />
                    Модерация
                  </label>
                </div>
              </div>
            </div>
          ) : null}

          {step === 2 ? (
            <div className='space-y-4'>
              <div>
                <div className='text-xs font-medium text-gray-500'>Fallback-приоритет (чем меньше – тем выше)</div>
                <Input
                  type='number'
                  placeholder='100'
                  value={internal.params.fallback_priority ?? ''}
                  onChange={(e) =>
                    setInternal((prev) =>
                      prev
                        ? {
                            ...prev,
                            params: {
                              ...prev.params,
                              fallback_priority: parseNumber(e.target.value, prev.params.fallback_priority ?? null),
                            },
                          }
                        : prev,
                    )
                  }
                />
              </div>
              <div>
                <div className='text-xs font-medium text-gray-500'>Режим работы (опционально)</div>
                <Select
                  value={internal.params.mode || ''}
                  onChange={(e: any) =>
                    setInternal((prev) =>
                      prev
                        ? {
                            ...prev,
                            params: {
                              ...prev.params,
                              mode: e.target.value || null,
                            },
                          }
                        : prev,
                    )
                  }
                >
                  <option value=''>Авто</option>
                  <option value='chat'>chat</option>
                  <option value='completion'>completion</option>
                  <option value='embedding'>embedding</option>
                </Select>
              </div>
              <div className='rounded-md border border-gray-200 bg-gray-50 p-4 text-xs text-gray-600 space-y-2'>
                <div className='font-medium text-gray-900'>Проверьте перед сохранением:</div>
                <ul className='list-disc space-y-1 pl-4'>
                  <li>Название модели совпадает с конфигурацией в сервисах.</li>
                  <li>Провайдер активен и содержит актуальный API ключ.</li>
                  <li>Лимиты соответствуют договору с провайдером.</li>
                  <li>Fallback-приоритет не конфликтует с существующими правилами.</li>
                </ul>
              </div>
            </div>
          ) : null}
        </div>
      ) : (
        <div className='p-6 text-sm text-gray-500'>Выберите модель для редактирования.</div>
      )}
    </Drawer>
  );
}

function updateField(
  setInternal: React.Dispatch<React.SetStateAction<ModelFormState | null>>,
  key: keyof ModelFormState,
  value: any,
) {
  setInternal((prev) => (prev ? { ...prev, [key]: value } : prev));
}

function parseNumber(value: string, fallback: number | null) {
  if (value === '') return null;
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return fallback;
  return numeric;
}

function normalizeNumber(value?: number | null) {
  if (value === null || value === undefined) return undefined;
  if (Number.isNaN(Number(value))) return undefined;
  return value;
}

type UsageKey = keyof NonNullable<ModelFormState['params']['usage']>;

function toggleUsage(
  setInternal: React.Dispatch<React.SetStateAction<ModelFormState | null>>,
  key: UsageKey,
) {
  setInternal((prev) =>
    prev
      ? {
          ...prev,
          params: {
            ...prev.params,
            usage: {
              ...(prev.params.usage || {}),
              [key]: !prev.params.usage?.[key],
            },
          },
        }
      : prev,
  );
}
