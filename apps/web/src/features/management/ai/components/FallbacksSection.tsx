import React from 'react';
import { Button, Card, Input, Select, Spinner, Table } from '@ui';
import type { FallbackRule, Model } from '../types';
import { Trash2 } from '@icons';

type FallbackDraft = {
  primary: string;
  fallback: string;
  mode: string;
  priority: number;
};

type FallbacksSectionProps = {
  models: Model[];
  fallbacks: FallbackRule[];
  draft: FallbackDraft;
  onDraftChange: (draft: FallbackDraft) => void;
  onCreateFallback: () => void;
  onRemoveFallback: (id: string) => void;
  saving: boolean;
  removingId: string | null;
};

export function FallbacksSection({
  models,
  fallbacks,
  draft,
  onDraftChange,
  onCreateFallback,
  onRemoveFallback,
  saving,
  removingId,
}: FallbacksSectionProps) {
  const modelOptions = React.useMemo(() => models.map((model) => ({ label: model.name, value: model.name })), [models]);

  const selectClass = 'h-11 rounded-full border-transparent bg-white/80 px-4 text-sm shadow-inner focus:border-primary-400 focus:ring-2 focus:ring-primary-200 dark:bg-slate-900/60';
  const inputClass = 'h-11 rounded-full border-transparent bg-white/80 px-4 text-sm shadow-inner focus:border-primary-400 focus:ring-2 focus:ring-primary-200 dark:bg-slate-900/60';

  return (
    <Card
      skin="none"
      className="rounded-2xl border border-white/50 bg-white/70 px-0 py-0 shadow-lg shadow-indigo-100/40 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/70 dark:shadow-none"
    >
      <div className="space-y-6 p-6 lg:p-8">
        <div className="flex flex-col gap-2">
          <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">Fallback-политики</div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Настройте цепочки переключения модели в случае ошибки, таймаута или исчерпания лимитов. Приоритет используется для выбора первого доступного fallback.
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-4">
          <div className="lg:col-span-1">
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">Primary модель</div>
            <Select
              value={draft.primary}
              onChange={(e: any) => onDraftChange({ ...draft, primary: e.target.value })}
              className={selectClass}
            >
              <option value="">Выберите модель</option>
              {modelOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="lg:col-span-1">
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">Fallback модель</div>
            <Select
              value={draft.fallback}
              onChange={(e: any) => onDraftChange({ ...draft, fallback: e.target.value })}
              className={selectClass}
            >
              <option value="">Выберите модель</option>
              {modelOptions.map((option) => (
                <option key={option.value} value={option.value} disabled={option.value === draft.primary}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="lg:col-span-1">
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">Режим</div>
            <Select value={draft.mode} onChange={(e: any) => onDraftChange({ ...draft, mode: e.target.value })} className={selectClass}>
              <option value="on_error">on_error</option>
              <option value="on_timeout">on_timeout</option>
              <option value="rate_limit">rate_limit</option>
            </Select>
          </div>
          <div className="lg:col-span-1">
            <div className="text-xs font-medium text-slate-500 dark:text-slate-400">Приоритет</div>
            <Input
              type="number"
              value={draft.priority}
              onChange={(e) =>
                onDraftChange({
                  ...draft,
                  priority: Number.isNaN(Number(e.target.value)) ? draft.priority : Number(e.target.value),
                })
              }
              className={inputClass}
            />
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Button
            className="rounded-full px-6"
            onClick={onCreateFallback}
            disabled={
              saving ||
              !draft.primary ||
              !draft.fallback ||
              draft.primary === draft.fallback
            }
          >
            {saving ? (
              <span className="flex items-center gap-2">
                <Spinner size="sm" />
                Сохраняем...
              </span>
            ) : (
              'Добавить правило'
            )}
          </Button>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Чем меньше приоритет – тем выше в цепочке (например, 10 выше 100).
          </span>
        </div>

        <div className="overflow-hidden rounded-2xl border border-white/60 bg-white/60 shadow-inner dark:border-slate-800 dark:bg-slate-900/60">
          <Table.Table className="min-w-full text-sm">
            <Table.THead>
              <Table.TR>
                {['Primary', 'Fallback', 'Режим', 'Приоритет', 'Создано', 'Действия'].map((label) => (
                  <Table.TH
                    key={label}
                    className="px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 first:pl-6 last:pr-6 dark:text-slate-400"
                  >
                    {label}
                  </Table.TH>
                ))}
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {fallbacks.length ? (
                fallbacks.map((rule) => (
                  <Table.TR
                    key={rule.id}
                    className="border-t border-white/60 bg-white/70 transition-colors hover:bg-primary-50/60 first:border-t-0 dark:border-slate-800 dark:bg-slate-900/60 dark:hover:bg-slate-800/60"
                  >
                    <Table.TD className="px-4 py-4 first:pl-6">{rule.primary_model}</Table.TD>
                    <Table.TD className="px-4 py-4">{rule.fallback_model}</Table.TD>
                    <Table.TD className="px-4 py-4">{rule.mode || 'on_error'}</Table.TD>
                    <Table.TD className="px-4 py-4">{rule.priority ?? '—'}</Table.TD>
                    <Table.TD className="px-4 py-4 text-xs text-slate-500 dark:text-slate-400">{rule.created_at || '—'}</Table.TD>
                    <Table.TD className="px-4 py-4 last:pr-6">
                      <div className="flex justify-end">
                        <Button
                          size="xs"
                          variant="ghost"
                          color="error"
                          className="h-8 w-8 rounded-full p-0 text-rose-600 hover:bg-rose-50"
                          disabled={removingId === rule.id}
                          onClick={() => onRemoveFallback(rule.id)}
                        >
                          {removingId === rule.id ? (
                            <Spinner size="sm" />
                          ) : (
                            <>
                              <Trash2 className="h-4 w-4" />
                              <span className="sr-only">Удалить правило</span>
                            </>
                          )}
                        </Button>
                      </div>
                    </Table.TD>
                  </Table.TR>
                ))
              ) : (
                <Table.TR>
                  <Table.TD colSpan={6} className="px-6 py-10 text-center text-sm text-slate-500 dark:text-slate-400">
                    Fallback-правила ещё не заданы.
                  </Table.TD>
                </Table.TR>
              )}
            </Table.TBody>
          </Table.Table>
        </div>
      </div>
    </Card>
  );
}
