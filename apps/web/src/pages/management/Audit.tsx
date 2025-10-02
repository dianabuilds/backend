import React from 'react';
import { AlertTriangle, FileCode2 } from '@icons';
import { Badge, Button, Card, Input, Select, Spinner, Surface, Table, TablePagination } from '@ui';
import { apiGet } from '../../shared/api/client';
import { usePaginatedQuery } from '../../shared/hooks/usePaginatedQuery';
import { extractErrorMessage } from '../../shared/utils/errors';
import { PlatformAdminFrame, PlatformAdminQuickLink } from './platform-admin/PlatformAdminFrame';

type AuditEventMeta = {
  module?: string;
  verb?: string;
  resource_label?: string;
  result?: string;
};

type AuditEvent = {
  id?: string;
  created_at?: string | null;
  actor_id?: string | null;
  action?: string | null;
  resource_type?: string | null;
  resource_id?: string | null;
  reason?: string | null;
  ip?: string | null;
  user_agent?: string | null;
  before?: unknown;
  after?: unknown;
  extra?: unknown;
  meta?: AuditEventMeta | null;
};

type AuditFacets = {
  modules?: Record<string, number>;
  resource_types?: Record<string, number>;
  results?: Record<string, number>;
};

type AuditResponse = {
  items: AuditEvent[];
  page: number;
  page_size: number;
  has_more: boolean;
  next_page?: number | null;
  facets?: AuditFacets;
  taxonomy?: {
    actions?: string[];
  };
};

type AuditFilters = {
  search: string;
  module: string;
  action: string;
  resourceType: string;
  result: string;
  actorId: string;
  dateFrom: string;
  dateTo: string;
};

type UserOption = {
  id: string;
  username?: string | null;
};

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];
const RESULT_OPTIONS = [
  { value: '', label: 'Все результаты' },
  { value: 'success', label: 'Успех' },
  { value: 'failure', label: 'Ошибка' },
];

function formatDateTime(value?: string | null): string {
  if (!value) return '';
  try {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
  } catch {
    return value;
  }
}

type ResultBadge = {
  label: string;
  color: 'success' | 'warning' | 'error' | 'neutral' | 'info';
};

function getResultBadge(result?: string | null): ResultBadge {
  const normalized = (result || '').toLowerCase();
  if (normalized === 'success') return { label: 'Успех', color: 'success' };
  if (normalized === 'failure') return { label: 'Ошибка', color: 'error' };
  if (normalized === 'warning') return { label: 'Внимание', color: 'warning' };
  return { label: normalized ? normalized : 'Неизвестно', color: 'neutral' };
}

function prettyJson(value: unknown): string {
  if (value == null) return '';
  if (typeof value === 'string') return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function calculateTotalItems(data: AuditResponse | null, page: number, pageSize: number): number | undefined {
  if (!data) return undefined;
  if (data.has_more) return undefined;
  const current = data.items?.length ?? 0;
  return (page - 1) * pageSize + current;
}

function topEntries(source: Record<string, number> | undefined, limit = 6): Array<[string, number]> {
  if (!source) return [];
  return Object.entries(source)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit);
}

export default function ManagementAudit() {
  const [data, setData] = React.useState<AuditResponse | null>(null);
  const [refreshToken, setRefreshToken] = React.useState(0);
  const [expandedId, setExpandedId] = React.useState<string | null>(null);

  const [filters, setFilters] = React.useState<AuditFilters>({
    search: '',
    module: '',
    action: '',
    resourceType: '',
    result: '',
    actorId: '',
    dateFrom: '',
    dateTo: '',
  });

  const [actorQuery, setActorQuery] = React.useState('');
  const [userOpts, setUserOpts] = React.useState<UserOption[]>([]);
  const [showUserOpts, setShowUserOpts] = React.useState(false);

  const {
    items,
    page,
    setPage,
    pageSize,
    setPageSize,
    hasNext,
    loading,
    error,
  } = usePaginatedQuery<AuditEvent, AuditResponse>({
    initialPageSize: 20,
    dependencies: [
      filters.search,
      filters.module,
      filters.action,
      filters.resourceType,
      filters.result,
      filters.actorId,
      filters.dateFrom,
      filters.dateTo,
      refreshToken,
    ],
    debounceMs: 250,
    fetcher: async ({ page: currentPage, pageSize: currentPageSize, signal }) => {
      const params = new URLSearchParams();
      params.set('page', String(currentPage));
      params.set('page_size', String(currentPageSize));
      if (filters.search.trim()) params.set('q', filters.search.trim());
      if (filters.module) params.set('module', filters.module);
      if (filters.action) params.set('action', filters.action);
      if (filters.resourceType) params.set('resource_type', filters.resourceType);
      if (filters.result) params.set('result', filters.result);
      if (filters.actorId) params.set('actor_id', filters.actorId);
      if (filters.dateFrom) params.set('from', filters.dateFrom);
      if (filters.dateTo) params.set('to', filters.dateTo);
      return apiGet<AuditResponse>(`/v1/audit?${params.toString()}`, { signal });
    },
    mapResponse: (response, { page: currentPage, pageSize: currentPageSize }) => {
      const nextItems = Array.isArray(response?.items) ? response.items : [];
      setData(response ?? null);
      if (nextItems.every((item) => item.id !== expandedId)) {
        setExpandedId(null);
      }
      const hasMore = Boolean(response?.has_more);
      const total = hasMore ? undefined : (currentPage - 1) * currentPageSize + nextItems.length;
      return {
        items: nextItems,
        hasNext: hasMore,
        total,
      };
    },
    onError: (err) => {
      setData(null);
      setExpandedId(null);
      return extractErrorMessage(err, '?? ??????? ????????? ?????');
    },
  });

  const updateFilter = React.useCallback(
    <K extends keyof AuditFilters>(key: K, value: AuditFilters[K]) => {
      setFilters((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  React.useEffect(() => {
    setPage(1);
  }, [
    setPage,
    filters.search,
    filters.module,
    filters.action,
    filters.resourceType,
    filters.result,
    filters.actorId,
    filters.dateFrom,
    filters.dateTo,
  ]);

  React.useEffect(() => {
    if (!actorQuery.trim()) {
      setUserOpts([]);
      return;
    }
    let alive = true;
    const handle = window.setTimeout(async () => {
      try {
        const response = await apiGet<UserOption[]>(`/v1/users/search?q=${encodeURIComponent(actorQuery.trim())}&limit=10`);
        if (!alive) return;
        if (Array.isArray(response)) setUserOpts(response);
      } catch {
        if (alive) setUserOpts([]);
      }
    }, 200);
    return () => {
      alive = false;
      window.clearTimeout(handle);
    };
  }, [actorQuery]);


  const moduleOptions = React.useMemo(() => {
    const entries = new Set<string>();
    Object.keys(data?.facets?.modules ?? {}).forEach((key) => entries.add(key));
    if (filters.module) entries.add(filters.module);
    return Array.from(entries).sort();
  }, [data?.facets?.modules, filters.module]);

  const actionOptions = React.useMemo(() => {
    const actions = data?.taxonomy?.actions || [];
    return actions.slice().sort((a, b) => a.localeCompare(b));
  }, [data?.taxonomy?.actions]);

  const resourceOptions = React.useMemo(() => {
    const entries = new Set<string>();
    Object.keys(data?.facets?.resource_types ?? {}).forEach((key) => entries.add(key));
    if (filters.resourceType) entries.add(filters.resourceType);
    return Array.from(entries).sort();
  }, [data?.facets?.resource_types, filters.resourceType]);

  const totalItems = calculateTotalItems(data, page, pageSize);
  const currentCount = items.length;

  const handleReset = React.useCallback(() => {
    setFilters({
      search: '',
      module: '',
      action: '',
      resourceType: '',
      result: '',
      actorId: '',
      dateFrom: '',
      dateTo: '',
    });
    setActorQuery('');
    setUserOpts([]);
    setExpandedId(null);
  }, []);

  const handleRefresh = React.useCallback(() => {
    setRefreshToken((prev) => prev + 1);
  }, []);

  const roleHint = (
    <div className="space-y-2 text-sm">
      <p>Доступ к аудиту имеет только роль <code>admin</code>.</p>
      <p className="text-xs text-gray-500 dark:text-dark-200">Если права отсутствуют, обратитесь к владельцу аккаунта за эскалацией.</p>
    </div>
  );

  const quickLinks: PlatformAdminQuickLink[] = [
    {
      label: 'Документация: аудит платформы',
      href: 'https://docs.caves.dev/platform/audit',
      description: 'Структура событий и принципы ведения журнала действий.',
      icon: <FileCode2 className="h-4 w-4" />,
    },
    {
      label: 'API reference: /v1/audit',
      href: 'https://docs.caves.dev/api/audit',
      description: 'Параметры фильтрации и примеры экспорта журнала.',
    },
  ];

  return (
    <PlatformAdminFrame
      title="Audit log"
      description="Журнал административных действий и системных операций по всей платформе."
      breadcrumbs={[
        { label: 'Platform Admin', to: '/platform/audit' },
        { label: 'Audit log' },
      ]}
      actions={
        <Button
          as="a"
          href="/v1/audit/export?format=csv&limit=2000"
          target="_blank"
          rel="noopener noreferrer"
          variant="outlined"
          color="primary"
          size="sm"
        >
          Экспорт CSV
        </Button>
      }
      roleHint={roleHint}
      quickLinks={quickLinks}
      helpText="Используйте фильтры, чтобы найти конкретное действие. Для расследований сохраняйте экспорт и прикладывайте в тикеты поддержки."
    >
      <Surface variant="soft" className="space-y-6 p-6">
        <div className="grid gap-4 lg:grid-cols-4">
          <Input
            label="Поиск"
            placeholder="Событие, ресурс или IP"
            value={filters.search}
            onChange={(event) => updateFilter('search', event.target.value)}
          />
          <Select
            value={filters.module}
            onChange={(event) => updateFilter('module', event.target.value)}
            className="h-[58px]"
          >
            <option value="">Все модули</option>
            {moduleOptions.map((option) => (
              <option key={option} value={option}>
                {option || '—'}
              </option>
            ))}
          </Select>
          <Select
            value={filters.action}
            onChange={(event) => updateFilter('action', event.target.value)}
            className="h-[58px]"
          >
            <option value="">Все действия</option>
            {actionOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </Select>
          <Select
            value={filters.resourceType}
            onChange={(event) => updateFilter('resourceType', event.target.value)}
            className="h-[58px]"
          >
            <option value="">Все ресурсы</option>
            {resourceOptions.map((option) => (
              <option key={option} value={option}>
                {option || '—'}
              </option>
            ))}
          </Select>
          <Select
            value={filters.result}
            onChange={(event) => updateFilter('result', event.target.value)}
            className="h-[58px]"
          >
            {RESULT_OPTIONS.map((option) => (
              <option key={option.value || 'all'} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <div className="relative">
            <Input
              label="Актор"
              placeholder="email или ID"
              value={actorQuery}
              onChange={(event) => {
                setActorQuery(event.target.value);
                setShowUserOpts(true);
              }}
              onFocus={() => setShowUserOpts(true)}
              onBlur={() => window.setTimeout(() => setShowUserOpts(false), 150)}
            />
            {filters.actorId ? (
              <button
                type="button"
                className="absolute right-3 top-9 text-xs text-gray-400 hover:text-gray-600"
                onClick={() => {
                  updateFilter('actorId', '');
                  setActorQuery('');
                }}
              >
                Очистить
              </button>
            ) : null}
            {showUserOpts && userOpts.length > 0 ? (
              <div className="absolute z-10 mt-1 max-h-56 w-full overflow-y-auto rounded-xl border border-gray-200 bg-white shadow-lg dark:border-dark-500 dark:bg-dark-700">
                {userOpts.map((user) => (
                  <button
                    key={user.id}
                    type="button"
                    className="flex w-full flex-col items-start gap-0.5 px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600"
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => {
                      updateFilter('actorId', user.id);
                      setActorQuery(user.username || user.id);
                      setShowUserOpts(false);
                    }}
                  >
                    <span className="font-medium text-gray-900 dark:text-white">{user.username || user.id}</span>
                    {user.username && user.username !== user.id ? (
                      <span className="text-xs text-gray-500 dark:text-dark-200">{user.id}</span>
                    ) : null}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
          <Input
            type="datetime-local"
            label="От"
            value={filters.dateFrom}
            onChange={(event) => updateFilter('dateFrom', event.target.value)}
          />
          <Input
            type="datetime-local"
            label="До"
            value={filters.dateTo}
            onChange={(event) => updateFilter('dateTo', event.target.value)}
          />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-gray-600 dark:text-dark-200">
          <span>
            Показано {currentCount} событий на странице.
            {hasNext ? ' Доступны следующие страницы.' : ''}
          </span>
          <div className="flex items-center gap-2">
            <Button variant="ghost" color="neutral" size="sm" onClick={handleReset}>
              Сбросить фильтры
            </Button>
            <Button variant="outlined" color="primary" size="sm" onClick={handleRefresh} disabled={loading}>
              Обновить
            </Button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <Table.Table className="min-w-[960px]" hover>
            <Table.THead>
              <Table.TR>
                <Table.TH className="w-48">Время</Table.TH>
                <Table.TH>Модуль</Table.TH>
                <Table.TH>Действие</Table.TH>
                <Table.TH>Ресурс</Table.TH>
                <Table.TH>Актор</Table.TH>
                <Table.TH className="w-28">Результат</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {loading ? (
                <Table.TR>
                  <Table.TD colSpan={6} className="py-6 text-center text-sm text-gray-500">
                    <div className="inline-flex items-center gap-3">
                      <Spinner size="sm" /> Загрузка событий...
                    </div>
                  </Table.TD>
                </Table.TR>
              ) : null}
              {error && !loading ? (
                <Table.TR>
                  <Table.TD colSpan={6} className="py-6 text-center text-sm text-rose-600 dark:text-rose-300">
                    {error}
                  </Table.TD>
                </Table.TR>
              ) : null}
              {!loading && !error && items.length === 0 ? (
                <Table.TR>
                  <Table.TD colSpan={6} className="py-6 text-center text-sm text-gray-500">
                    Нет событий для выбранных фильтров.
                  </Table.TD>
                </Table.TR>
              ) : null}
              {items.map((item, index) => {
                const rowId = item.id || `row-${index}`;
                const badge = getResultBadge(item.meta?.result);
                const module = item.meta?.module || '—';
                const verb = item.meta?.verb || '';
                const resourceLabel = item.meta?.resource_label || [item.resource_type, item.resource_id].filter(Boolean).join(':');
                return (
                  <React.Fragment key={rowId}>
                    <Table.TR
                      className="cursor-pointer align-top hover:bg-gray-50/70 dark:hover:bg-dark-700"
                      onClick={() => setExpandedId((prev) => (prev === rowId ? null : rowId))}
                    >
                      <Table.TD className="text-xs text-gray-500 dark:text-dark-200">{formatDateTime(item.created_at)}</Table.TD>
                      <Table.TD className="text-sm font-medium text-gray-700 dark:text-white">{module}</Table.TD>
                      <Table.TD className="text-sm text-gray-700 dark:text-dark-100">{item.action || verb || '—'}</Table.TD>
                      <Table.TD className="text-sm text-gray-600 dark:text-dark-100">{resourceLabel || '—'}</Table.TD>
                      <Table.TD className="text-sm text-gray-600 dark:text-dark-100">{item.actor_id || '—'}</Table.TD>
                      <Table.TD>
                        <Badge color={badge.color} variant="soft" className="uppercase tracking-wide">
                          {badge.label}
                        </Badge>
                      </Table.TD>
                    </Table.TR>
                    {expandedId === rowId ? (
                      <Table.TR>
                        <Table.TD colSpan={6} className="bg-gray-50/70 px-6 py-4 text-xs text-gray-700 dark:bg-dark-800 dark:text-dark-100">
                          <div className="grid gap-4 md:grid-cols-2">
                            <div>
                              <h4 className="mb-2 font-semibold text-gray-800 dark:text-white">Контекст</h4>
                              <dl className="grid gap-2">
                                <div className="flex justify-between gap-2">
                                  <dt className="text-gray-500 dark:text-dark-200">IP</dt>
                                  <dd>{item.ip || '—'}</dd>
                                </div>
                                <div className="flex justify-between gap-2">
                                  <dt className="text-gray-500 dark:text-dark-200">User agent</dt>
                                  <dd className="truncate" title={item.user_agent || undefined}>
                                    {item.user_agent || '—'}
                                  </dd>
                                </div>
                                <div className="flex justify-between gap-2">
                                  <dt className="text-gray-500 dark:text-dark-200">Причина</dt>
                                  <dd>{item.reason || (typeof item.extra === 'object' && (item.extra as any)?.reason) || '—'}</dd>
                                </div>
                              </dl>
                            </div>
                            <div>
                              <h4 className="mb-2 font-semibold text-gray-800 dark:text-white">Дополнительно</h4>
                              <pre className="max-h-48 overflow-auto rounded-lg bg-white/80 p-3 text-[11px] leading-relaxed text-gray-800 shadow-inner dark:bg-dark-900 dark:text-dark-50">
                                {prettyJson(item.extra) || '—'}
                              </pre>
                            </div>
                            <div>
                              <h4 className="mb-2 font-semibold text-gray-800 dark:text-white">Было</h4>
                              <pre className="max-h-48 overflow-auto rounded-lg bg-white/80 p-3 text-[11px] leading-relaxed text-gray-800 shadow-inner dark:bg-dark-900 dark:text-dark-50">
                                {prettyJson(item.before) || '—'}
                              </pre>
                            </div>
                            <div>
                              <h4 className="mb-2 font-semibold text-gray-800 dark:text-white">Стало</h4>
                              <pre className="max-h-48 overflow-auto rounded-lg bg-white/80 p-3 text-[11px] leading-relaxed text-gray-800 shadow-inner dark:bg-dark-900 dark:text-dark-50">
                                {prettyJson(item.after) || '—'}
                              </pre>
                            </div>
                          </div>
                        </Table.TD>
                      </Table.TR>
                    ) : null}
                  </React.Fragment>
                );
              })}
            </Table.TBody>
          </Table.Table>
        </div>

        <TablePagination
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={(value) => {
            setPageSize(value);
            setPage(1);
          }}
          currentCount={currentCount}
          hasNext={hasNext}
          totalItems={totalItems}
          pageSizeOptions={PAGE_SIZE_OPTIONS}
        />
      </Surface>

      <Card className="space-y-6 p-6">
        <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
          <AlertTriangle className="h-5 w-5 text-primary-500" />
          Сводка по событиям
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Модули</h4>
            {topEntries(data?.facets?.modules).length === 0 ? (
              <div className="rounded-lg border border-dashed border-gray-200 px-3 py-3 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-200">
                Детализация появится после первых событий.
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {topEntries(data?.facets?.modules).map(([module, count]) => (
                  <Badge key={module} color="neutral" variant="soft">
                    {module || '—'} · {count}
                  </Badge>
                ))}
              </div>
            )}
          </div>
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Результаты</h4>
            {topEntries(data?.facets?.results).length === 0 ? (
              <div className="rounded-lg border border-dashed border-gray-200 px-3 py-3 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-200">
                Будут доступны после загрузки событий.
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {topEntries(data?.facets?.results).map(([result, count]) => {
                  const badge = getResultBadge(result);
                  return (
                    <Badge key={result} color={badge.color} variant="soft">
                      {badge.label} · {count}
                    </Badge>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </Card>
    </PlatformAdminFrame>
  );
}
