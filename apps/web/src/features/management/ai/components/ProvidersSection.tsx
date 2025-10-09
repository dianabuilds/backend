import React from 'react';
import { Badge, Button, Card, Input, Switch, Table } from '@ui';
import type { Provider } from '../types';
import { Settings2 } from '@icons';

type ProvidersSectionProps = {
  providers: Provider[];
  hasProviderAccess: boolean;
  busyProviderSlug: string | null;
  onToggleProvider: (provider: Provider) => void;
  onOpenProvider: (provider?: Provider) => void;
};

export function ProvidersSection({
  providers,
  hasProviderAccess,
  busyProviderSlug,
  onToggleProvider,
  onOpenProvider,
}: ProvidersSectionProps) {
  const [search, setSearch] = React.useState('');

  const filtered = React.useMemo(() => {
    if (!search.trim()) return providers;
    const needle = search.trim().toLowerCase();
    return providers.filter((provider) =>
      [provider.slug, provider.title || '', provider.base_url || '']
        .filter(Boolean)
        .some((value) => value.toLowerCase().includes(needle)),
    );
  }, [providers, search]);

  return (
    <Card
      skin="none"
      className="rounded-2xl border border-white/50 bg-white/70 px-0 py-0 shadow-lg shadow-indigo-100/40 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/70 dark:shadow-none"
    >
      <div className="space-y-5 p-6 lg:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">Провайдеры</div>
            <p className="mt-1 max-w-xl text-xs text-slate-500 dark:text-slate-400">
              Управляйте подключениями к внешним AI-сервисам. Включайте/выключайте их и обновляйте ключи доступа.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск по slug или названию"
              className="h-11 min-w-[240px] rounded-full border-transparent bg-white/70 text-sm shadow-inner focus:border-primary-400 focus:ring-2 focus:ring-primary-200 dark:bg-slate-900/60"
            />
            {hasProviderAccess ? (
              <Button className="rounded-full px-5" onClick={() => onOpenProvider()}>
                Новый провайдер
              </Button>
            ) : null}
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-indigo-200/70 bg-white/50 p-10 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900/50">
            {providers.length === 0 ? 'Провайдеры ещё не подключены.' : 'По заданным условиям ничего не найдено.'}
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-white/60 bg-white/60 shadow-inner dark:border-slate-800 dark:bg-slate-900/60">
            <Table.Table className="min-w-full text-sm">
              <Table.THead>
                <Table.TR>
                  {['Статус', 'Провайдер', 'Endpoint', 'Timeout', 'Retries', 'Действия'].map((label) => (
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
                {filtered.map((provider) => {
                  const enabled = provider.enabled !== false;
                  return (
                    <Table.TR
                      key={provider.slug}
                      className="border-t border-white/60 bg-white/70 transition-colors hover:bg-primary-50/60 first:border-t-0 dark:border-slate-800 dark:bg-slate-900/60 dark:hover:bg-slate-800/60"
                    >
                      <Table.TD className="px-4 py-4 first:pl-6">
                        <Switch
                          checked={enabled}
                          disabled={!hasProviderAccess || busyProviderSlug === provider.slug}
                          onChange={() => onToggleProvider(provider)}
                          aria-label="Переключить провайдера"
                        />
                      </Table.TD>
                      <Table.TD className="px-4 py-4">
                        <div className="flex flex-col text-sm">
                          <span className="font-medium text-slate-900 dark:text-slate-100">{provider.slug}</span>
                          <span className="text-xs text-slate-500 dark:text-slate-400">{provider.title || '—'}</span>
                        </div>
                      </Table.TD>
                      <Table.TD className="px-4 py-4 text-xs text-slate-600 dark:text-slate-300">
                        {provider.base_url || '—'}
                      </Table.TD>
                      <Table.TD className="px-4 py-4 text-sm text-slate-600 dark:text-slate-300">
                        {provider.timeout_sec != null ? `${provider.timeout_sec}s` : '—'}
                      </Table.TD>
                      <Table.TD className="px-4 py-4 text-sm text-slate-600 dark:text-slate-300">
                        {provider.extras?.retries != null ? provider.extras.retries : '—'}
                      </Table.TD>
                      <Table.TD className="px-4 py-4 last:pr-6">
                        {hasProviderAccess ? (
                          <div className="flex items-center justify-end gap-2">
                            <Badge
                              variant="soft"
                              color={enabled ? 'success' : 'neutral'}
                              className="rounded-full px-2 py-0.5 text-[11px]"
                            >
                              {enabled ? 'В работе' : 'Выключен'}
                            </Badge>
                            <Button
                              size="xs"
                              variant="ghost"
                              className="h-8 w-8 rounded-full p-0 text-primary-600 hover:bg-primary-50"
                              onClick={() => onOpenProvider(provider)}
                            >
                              <Settings2 className="h-4 w-4" />
                              <span className="sr-only">Настроить провайдера</span>
                            </Button>
                          </div>
                        ) : (
                          <div className="flex justify-end">
                            <Badge variant="soft" color="neutral" className="rounded-full px-2 py-0.5 text-[11px]">
                              Только просмотр
                            </Badge>
                          </div>
                        )}
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
