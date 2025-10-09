import React from 'react';
import { Badge, Button, Card, Input, Switch, Table } from '@ui';
import type { FallbackRule, Model, Provider, UsageRow } from '../types';
import { BarChart3, Edit3, Trash2 } from '@icons';

type ModelsSectionProps = {
  models: Model[];
  providers: Provider[];
  usageRows: UsageRow[];
  fallbackByPrimary: Map<string, FallbackRule[]>;
  fallbackBySecondary: Map<string, FallbackRule[]>;
  busyModelId: string | null;
  onCreateModel: () => void;
  onEditModel: (model: Model) => void;
  onToggleModel: (model: Model) => void;
  onDeleteModel: (model: Model) => void;
};

export function ModelsSection({
  models,
  providers,
  usageRows,
  fallbackByPrimary,
  fallbackBySecondary,
  busyModelId,
  onCreateModel,
  onEditModel,
  onToggleModel,
  onDeleteModel,
}: ModelsSectionProps) {
  const [search, setSearch] = React.useState('');
  const filtered = React.useMemo(() => {
    if (!search.trim()) return models;
    const needle = search.trim().toLowerCase();
    return models.filter((model) => {
      const provider = providers.find((p) => p.slug === model.provider_slug);
      const fallbackRefs = fallbackByPrimary.get(model.name) || [];
      const fallbackRefsSecondary = fallbackBySecondary.get(model.name) || [];
      return [
        model.name,
        model.id,
        model.provider_slug,
        provider?.title || '',
        model.version || '',
        fallbackRefs.map((r) => r.fallback_model).join(','),
        fallbackRefsSecondary.map((r) => r.primary_model).join(','),
      ]
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(needle));
    });
  }, [models, providers, fallbackByPrimary, fallbackBySecondary, search]);

  return (
    <Card
      skin="none"
      className="rounded-2xl border border-white/50 bg-white/70 px-0 py-0 shadow-lg shadow-indigo-100/40 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/70 dark:shadow-none"
    >
      <div className="space-y-5 p-6 lg:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">Модели</div>
            <p className="mt-1 max-w-2xl text-xs text-slate-500 dark:text-slate-400">
              Здесь отображаются все LLM, доступные платформе. Управляйте статусами, лимитами и fallback-сценариями в одном месте.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Быстрый поиск по имени или провайдеру"
              className="h-11 min-w-[240px] rounded-full border-transparent bg-white/70 text-sm shadow-inner focus:border-primary-400 focus:ring-2 focus:ring-primary-200 dark:bg-slate-900/60"
            />
            <Button className="rounded-full px-5" onClick={onCreateModel}>
              Добавить модель
            </Button>
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-indigo-200/70 bg-white/50 p-10 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900/50">
            {models.length === 0 ? 'Пока нет ни одной модели. Создайте первую, чтобы сервисы смогли вызывать LLM.' : 'По заданным условиям ничего не найдено.'}
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-white/60 bg-white/60 shadow-inner dark:border-slate-800 dark:bg-slate-900/60">
            <Table.Table className="min-w-full text-sm">
              <Table.THead>
                <Table.TR className="bg-transparent">
                  {['Статус', 'Модель', 'Провайдер', 'Версия', 'Назначение', 'Лимиты', 'Нагрузка', 'Fallback', 'Действия'].map((label) => (
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
                {filtered.map((model) => {
                  const key = `${model.provider_slug}:${model.name}`;
                  const usage = usageRows.find((row) => row.key === key);
                  const limits = model.params?.limits || {};
                  const usageLabels = [
                    model.params?.usage?.content ? 'Контент' : null,
                    model.params?.usage?.quests ? 'AI-квесты' : null,
                    model.params?.usage?.moderation ? 'Модерация' : null,
                  ].filter(Boolean) as string[];
                  const fallbacksForModel = fallbackByPrimary.get(model.name) || [];
                  const fallbacksWhereUsed = fallbackBySecondary.get(model.name) || [];
                  const enabled = (model.status || 'active') !== 'disabled';
                  const provider = providers.find((p) => p.slug === model.provider_slug);

                  return (
                    <Table.TR
                      key={model.id}
                      className="border-t border-white/60 bg-white/70 transition-colors hover:bg-primary-50/60 first:border-t-0 dark:border-slate-800 dark:bg-slate-900/60 dark:hover:bg-slate-800/60"
                    >
                      <Table.TD className="px-4 py-4 first:pl-6">
                        <Switch
                          checked={enabled}
                          disabled={busyModelId === model.id}
                          onChange={() => onToggleModel(model)}
                          aria-label="Переключить модель"
                        />
                      </Table.TD>
                      <Table.TD className="px-4 py-4">
                        <div className="flex flex-col text-sm">
                          <span className="font-semibold text-slate-900 dark:text-slate-50">{model.name}</span>
                          <span className="text-xs font-mono text-slate-500 dark:text-slate-400">{model.id}</span>
                          {model.is_default ? (
                            <Badge color="primary" className="mt-2 w-max rounded-full px-2 py-0.5 text-[11px]">
                              Default
                            </Badge>
                          ) : null}
                          {fallbacksWhereUsed.length ? (
                            <Badge
                             
                              variant="soft"
                              color="neutral"
                              className="mt-2 w-max rounded-full px-2 py-0.5 text-[11px]"
                              title={`Используется как fallback у: ${fallbacksWhereUsed.map((rule) => rule.primary_model).join(', ')}`}
                            >
                              Используется в {fallbacksWhereUsed.length}
                            </Badge>
                          ) : null}
                        </div>
                      </Table.TD>
                      <Table.TD className="px-4 py-4">
                        <div className="flex flex-col text-sm">
                          <span className="font-medium text-slate-900 dark:text-slate-100">{provider?.title || provider?.slug || '—'}</span>
                          <span className="text-xs text-slate-500 dark:text-slate-400">{model.provider_slug}</span>
                        </div>
                      </Table.TD>
                      <Table.TD className="px-4 py-4 text-sm text-slate-600 dark:text-slate-300">{model.version || '—'}</Table.TD>
                      <Table.TD className="px-4 py-4">
                        {usageLabels.length ? (
                          <div className="flex flex-wrap gap-2">
                            {usageLabels.map((label) => (
                              <Badge key={label} variant="soft" color="neutral" className="rounded-full px-2 py-0.5 text-[11px]">
                                {label}
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400">Не назначено</span>
                        )}
                      </Table.TD>
                      <Table.TD className="px-4 py-4">
                        <div className="text-xs leading-5 text-slate-600 dark:text-slate-300">
                          {limits.daily_tokens != null ? <div>день: {limits.daily_tokens}</div> : null}
                          {limits.monthly_tokens != null ? <div>месяц: {limits.monthly_tokens}</div> : null}
                          {model.params?.fallback_priority != null ? <div>приоритет: {model.params?.fallback_priority}</div> : null}
                        </div>
                      </Table.TD>
                      <Table.TD className="px-4 py-4">
                        {usage ? (
                          <div className="text-xs leading-5 text-slate-600 dark:text-slate-300">
                            <div>calls: {usage.calls}</div>
                            <div className={usage.errors ? 'font-medium text-rose-600 dark:text-rose-400' : ''}>errors: {usage.errors}</div>
                            <div>tokens: {usage.promptTokens + usage.completionTokens}</div>
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400">нет данных</span>
                        )}
                      </Table.TD>
                      <Table.TD className="px-4 py-4">
                        {fallbacksForModel.length ? (
                          <div className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
                            {fallbacksForModel.map((rule) => (
                              <div key={rule.id} className="flex items-center gap-2">
                                <span aria-hidden="true" className="text-primary-500">&rarr;</span>
                                <span>
                                  {rule.fallback_model} {rule.mode ? `(${rule.mode})` : ''}
                                </span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </Table.TD>
                      <Table.TD className="px-4 py-4 last:pr-6">
                        <div className="flex flex-wrap items-center justify-end gap-2">
                          <Button
                            size="xs"
                            variant="ghost"
                            className="h-8 w-8 rounded-full p-0 text-primary-600 hover:bg-primary-50"
                            onClick={() => onEditModel(model)}
                          >
                            <Edit3 className="h-4 w-4" />
                            <span className="sr-only">Редактировать модель</span>
                          </Button>
                          <Button
                            size="xs"
                            variant="ghost"
                            color="neutral"
                            className="h-8 w-8 rounded-full p-0 text-slate-500 hover:bg-slate-100"
                            as="a"
                            href="/observability/llm"
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <BarChart3 className="h-4 w-4" />
                            <span className="sr-only">Перейти к метрикам</span>
                          </Button>
                          <Button
                            size="xs"
                            variant="ghost"
                            color="error"
                            className="h-8 w-8 rounded-full p-0 text-rose-600 hover:bg-rose-50"
                            disabled={busyModelId === model.id}
                            onClick={() => onDeleteModel(model)}
                          >
                            <Trash2 className="h-4 w-4" />
                            <span className="sr-only">Удалить модель</span>
                          </Button>
                        </div>
                      </Table.TD>
                    </Table.TR>
                  );
                })}
              </Table.TBody>
            </Table.Table>
          </div>
        )}
      </div>
    </Card>
  );
}
