import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { Button, Card, Spinner, TablePagination, useToast } from '@ui';
import { useAuth } from '@shared/auth';
import { apiGet, apiPatch } from '@shared/api/client';
import { formatDateTime } from '@shared/utils/format';
import { CaseFilters } from './CaseFilters';
import { CaseTable } from './CaseTable';
import { CasePreviewDrawer } from './CasePreviewDrawer';
import { useModerationCase } from './hooks';
import type { CaseFiltersState, CasesListResponse, ModerationCaseDetail, ModerationCaseSummary } from './types';

const DEFAULT_PAGE_SIZE = 10;
const AUTO_REFRESH_INTERVAL_MS = 60_000;

function parseCsv(value: string | null): string[] {
  if (!value) return [];
  return value
    .split(',')
    .map((v) => v.trim())
    .filter(Boolean);
}

function buildFilters(params: URLSearchParams): CaseFiltersState {
  return {
    query: params.get('q') || '',
    statuses: parseCsv(params.get('statuses')),
    types: parseCsv(params.get('types')),
    queues: parseCsv(params.get('queues')),
    severities: parseCsv(params.get('severities')),
    priorities: parseCsv(params.get('priorities')),
    assignee: params.get('assignee') || '',
    tags: parseCsv(params.get('tags')),
  };
}

function toNumber(value: string | null, fallback: number) {
  const num = Number(value);
  return Number.isFinite(num) && num > 0 ? num : fallback;
}

export function CasesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  const { pushToast } = useToast();
  const filters = React.useMemo(() => buildFilters(searchParams), [searchParams]);
  const page = React.useMemo(() => toNumber(searchParams.get('page'), 1), [searchParams]);
  const pageSize = React.useMemo(() => toNumber(searchParams.get('size'), DEFAULT_PAGE_SIZE), [searchParams]);
  const selectedCaseId = searchParams.get('case');

  const currentUserId = React.useMemo(() => {
    if (!user) return '';
    return (user as any).id || (user as any).sub || '';
  }, [user]);

  const [items, setItems] = React.useState<ModerationCaseSummary[]>([]);
  const [totalItems, setTotalItems] = React.useState<number | undefined>(undefined);
  const [hasNext, setHasNext] = React.useState<boolean>(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [lastLoadedAt, setLastLoadedAt] = React.useState<string>('');
  const [autoRefresh, setAutoRefresh] = React.useState(false);
  const [bulkBusy, setBulkBusy] = React.useState(false);
  const [selectedCaseIds, setSelectedCaseIds] = React.useState<Set<string>>(new Set());

  const {
    caseId,
    data: caseDetail,
    loading: detailLoading,
    error: detailError,
    load: loadCase,
    update: updateCase,
    addNote: addCaseNote,
    select: selectCase,
  } = useModerationCase(selectedCaseId);

  const updateSearchParams = React.useCallback(
    (draft: Partial<CaseFiltersState> & { page?: number; size?: number; caseId?: string | null }) => {
      const next = new URLSearchParams(searchParams);
      const merged: CaseFiltersState = { ...filters, ...draft } as CaseFiltersState;

      if ('query' in draft) {
        if (merged.query) next.set('q', merged.query);
        else next.delete('q');
      }
      if ('statuses' in draft) {
        if (merged.statuses.length) next.set('statuses', merged.statuses.join(','));
        else next.delete('statuses');
      }
      if ('types' in draft) {
        if (merged.types.length) next.set('types', merged.types.join(','));
        else next.delete('types');
      }
      if ('queues' in draft) {
        if (merged.queues.length) next.set('queues', merged.queues.join(','));
        else next.delete('queues');
      }
      if ('severities' in draft) {
        if (merged.severities.length) next.set('severities', merged.severities.join(','));
        else next.delete('severities');
      }
      if ('priorities' in draft) {
        if (merged.priorities.length) next.set('priorities', merged.priorities.join(','));
        else next.delete('priorities');
      }
      if ('tags' in draft) {
        if (merged.tags.length) next.set('tags', merged.tags.join(','));
        else next.delete('tags');
      }
      if ('assignee' in draft) {
        if (merged.assignee) next.set('assignee', merged.assignee);
        else next.delete('assignee');
      }

      const filtersChanged =
        draft.query !== undefined ||
        draft.statuses !== undefined ||
        draft.types !== undefined ||
        draft.queues !== undefined ||
        draft.severities !== undefined ||
        draft.priorities !== undefined ||
        draft.tags !== undefined ||
        draft.assignee !== undefined;

      if ('page' in draft) {
        next.set('page', String(draft.page ?? 1));
      } else if (filtersChanged) {
        next.set('page', '1');
      }
      if ('size' in draft) {
        next.set('size', String(draft.size ?? DEFAULT_PAGE_SIZE));
      }
      if ('caseId' in draft) {
        const value = draft.caseId;
        if (value) next.set('case', value);
        else next.delete('case');
      }

      setSearchParams(next, { replace: true });
    },
    [filters, searchParams, setSearchParams],
  );

  const loadCases = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: string[] = [`page=${page}`, `size=${pageSize}`];
      if (filters.statuses.length) params.push(`statuses=${encodeURIComponent(filters.statuses.join(','))}`);
      if (filters.types.length) params.push(`types=${encodeURIComponent(filters.types.join(','))}`);
      if (filters.queues.length) params.push(`queues=${encodeURIComponent(filters.queues.join(','))}`);
      if (filters.assignee) params.push(`assignee=${encodeURIComponent(filters.assignee)}`);
      if (filters.query) params.push(`q=${encodeURIComponent(filters.query)}`);
      if (filters.severities.length) params.push(`severities=${encodeURIComponent(filters.severities.join(','))}`);
      if (filters.priorities.length) params.push(`priorities=${encodeURIComponent(filters.priorities.join(','))}`);
      if (filters.tags.length) params.push(`tags=${encodeURIComponent(filters.tags.join(','))}`);
      const res = await apiGet<CasesListResponse>(`/v1/moderation/cases?${params.join('&')}`);
      const list = Array.isArray(res?.items) ? res.items : [];
      setItems(list);
      const total = typeof res?.total === 'number' ? res.total : undefined;
      setTotalItems(total);
      if (total != null) {
        setHasNext(page * pageSize < total);
      } else {
        setHasNext(list.length === pageSize);
      }
      setLastLoadedAt(new Date().toISOString());
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
      setItems([]);
      setTotalItems(undefined);
      setHasNext(false);
    } finally {
      setLoading(false);
    }
  }, [
    filters.assignee,
    filters.priorities,
    filters.queues,
    filters.query,
    filters.severities,
    filters.statuses,
    filters.tags,
    filters.types,
    page,
    pageSize,
  ]);

  React.useEffect(() => {
    void loadCases();
  }, [loadCases]);

  React.useEffect(() => {
    if (!selectedCaseId) {
      selectCase(null);
      return;
    }
    selectCase(selectedCaseId);
    void loadCase(selectedCaseId, { force: true });
  }, [selectedCaseId, selectCase, loadCase]);

  React.useEffect(() => {
    if (!autoRefresh) return;
    const intervalId = window.setInterval(() => {
      void loadCases();
    }, AUTO_REFRESH_INTERVAL_MS);
    return () => window.clearInterval(intervalId);
  }, [autoRefresh, loadCases]);

  const clientFilteredItems = React.useMemo(() => {
    return items.filter((item) => {
      if (filters.severities.length && !filters.severities.includes(String(item.severity || '').toLowerCase())) {
        return false;
      }
      if (filters.priorities.length && !filters.priorities.includes(String(item.priority || '').toLowerCase())) {
        return false;
      }
      if (filters.tags.length) {
        const tags = Array.isArray(item.tags) ? item.tags.map((t) => String(t).toLowerCase()) : [];
        if (!filters.tags.every((tag) => tags.includes(tag.toLowerCase()))) return false;
      }
      return true;
    });
  }, [items, filters.severities, filters.priorities, filters.tags]);

  const stats = React.useMemo(() => {
    const total = totalItems ?? clientFilteredItems.length;
    const open = clientFilteredItems.filter((c) => String(c.status || '').toLowerCase() === 'open').length;
    const unassigned = clientFilteredItems.filter((c) => !c.assignee_id).length;
    return { total, open, unassigned };
  }, [clientFilteredItems, totalItems]);

  React.useEffect(() => {
    setSelectedCaseIds((prev) => {
      const retained = new Set<string>();
      clientFilteredItems.forEach((item) => {
        if (prev.has(item.id)) retained.add(item.id);
      });
      if (retained.size === prev.size && Array.from(prev).every((id) => retained.has(id))) {
        return prev;
      }
      return retained;
    });
  }, [clientFilteredItems]);

  const handleSelectCase = (item: ModerationCaseSummary) => {
    updateSearchParams({ caseId: item.id });
  };

  const handleToggleRow = React.useCallback((id: string, checked: boolean) => {
    setSelectedCaseIds((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  }, []);

  const handleToggleAll = React.useCallback(
    (checked: boolean) => {
      if (!checked) {
        setSelectedCaseIds(new Set());
        return;
      }
      setSelectedCaseIds(new Set(clientFilteredItems.map((item) => item.id)));
    },
    [clientFilteredItems],
  );

  const closeDrawer = () => {
    updateSearchParams({ caseId: null });
  };

  const refreshDetail = React.useCallback(async () => {
    await Promise.all([
      loadCases(),
      caseId ? loadCase(caseId, { force: true }) : Promise.resolve(null),
    ]);
  }, [loadCases, loadCase, caseId]);

  const handleUpdateCase = React.useCallback(
    async (payload: Record<string, any>) => {
      await updateCase(payload);
      await refreshDetail();
    },
    [updateCase, refreshDetail],
  );

  const handleAddNote = React.useCallback(
    async ({ text, pinned }: { text: string; pinned?: boolean }) => {
      await addCaseNote({ text, pinned: pinned, visibility: 'internal' });
      await refreshDetail();
    },
    [addCaseNote, refreshDetail],
  );

  const lastLoadedLabel = lastLoadedAt ? formatDateTime(lastLoadedAt) : '-';
  const selectedCount = selectedCaseIds.size;
  const autoRefreshHint = autoRefresh ? 'Auto refresh enabled (1 min cadence)' : 'Manual refresh';

  const performBulkUpdate = React.useCallback(
    async (builder: (caseId: string) => Record<string, any> | null | undefined) => {
      const ids = Array.from(selectedCaseIds);
      if (!ids.length) return;
      setBulkBusy(true);
      try {
        const results = await Promise.allSettled(
          ids.map(async (id) => {
            const payload = builder(id);
            if (!payload || Object.keys(payload).length === 0) {
              return null;
            }
            await apiPatch(`/v1/moderation/cases/${encodeURIComponent(id)}`, payload);
            return id;
          }),
        );
        const succeeded = results.filter((result) => result.status === 'fulfilled').length;
        const failed = results.length - succeeded;
        if (succeeded) {
          pushToast({ intent: 'success', description: `Updated ${succeeded} case${succeeded === 1 ? '' : 's'}.` });
        }
        if (failed) {
          pushToast({ intent: 'info', description: `${failed} case${failed === 1 ? '' : 's'} failed to update.` });
        }
        setSelectedCaseIds(new Set());
        await refreshDetail();
      } catch (err: any) {
        pushToast({ intent: 'error', description: String(err?.message || err || 'Bulk update failed') });
      } finally {
        setBulkBusy(false);
      }
    },
    [pushToast, refreshDetail, selectedCaseIds],
  );

  const handleAssignToMe = React.useCallback(() => {
    if (!currentUserId) {
      pushToast({ intent: 'info', description: 'Cannot assign: user id not available.' });
      return;
    }
    void performBulkUpdate(() => ({ assignee_id: currentUserId }));
  }, [currentUserId, performBulkUpdate, pushToast]);

  const handleMarkResolved = React.useCallback(() => {
    void performBulkUpdate(() => ({ status: 'resolved' }));
  }, [performBulkUpdate]);

  const handleEscalate = React.useCallback(() => {
    void performBulkUpdate(() => ({ status: 'escalated' }));
  }, [performBulkUpdate]);

  const handleClearSelection = React.useCallback(() => {
    setSelectedCaseIds(new Set());
  }, []);

  return (
    <div className="space-y-5 p-6">
      <CaseFilters
        filters={filters}
        onChange={(next) => updateSearchParams(next)}
        onReset={() => setSearchParams(new URLSearchParams())}
        loading={loading}
        stats={stats}
        autoRefresh={autoRefresh}
        onAutoRefreshChange={setAutoRefresh}
      />

      <Card skin="shadow" className="space-y-4 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-xs text-gray-500">
            Updated: {lastLoadedLabel} · {autoRefreshHint}
          </div>
          <div className="flex items-center gap-2">
            {loading && <Spinner size="sm" />}
            <Button variant="ghost" color="neutral" onClick={() => void loadCases()} disabled={loading}>
              Refresh
            </Button>
          </div>
        </div>
        {error && <div className="rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}
        <CaseTable
          items={clientFilteredItems}
          onSelect={handleSelectCase}
          selectedId={selectedCaseId}
          selectedIds={selectedCaseIds}
          onToggleSelect={handleToggleRow}
          onToggleAll={handleToggleAll}
          disabled={bulkBusy}
        />
        <TablePagination
          page={page}
          pageSize={pageSize}
          currentCount={clientFilteredItems.length}
          totalItems={totalItems}
          hasNext={hasNext}
          onPageChange={(nextPage) => updateSearchParams({ page: nextPage })}
          onPageSizeChange={(size) => updateSearchParams({ size, page: 1 })}
        />
      </Card>

      <CasePreviewDrawer
        open={!!selectedCaseId}
        loading={detailLoading}
        data={caseDetail as ModerationCaseDetail | null}
        error={detailError}
        onClose={closeDrawer}
        onRefresh={refreshDetail}
        onUpdate={handleUpdateCase}
        onAddInternalNote={handleAddNote}
      />

      {selectedCount ? (
        <div className="fixed bottom-6 left-1/2 z-40 w-full max-w-3xl -translate-x-1/2">
          <Card skin="shadow" className="flex flex-wrap items-center justify-between gap-3 border border-gray-200 bg-white/95 p-4 shadow-lg dark:border-dark-700/70 dark:bg-dark-900/95">
            <div className="text-sm font-medium text-gray-700 dark:text-dark-100">
              {selectedCount} case{selectedCount === 1 ? '' : 's'} selected
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button size="sm" variant="outlined" onClick={handleAssignToMe} disabled={bulkBusy}>
                Assign to me
              </Button>
              <Button size="sm" variant="outlined" onClick={handleMarkResolved} disabled={bulkBusy}>
                Mark resolved
              </Button>
              <Button size="sm" variant="outlined" onClick={handleEscalate} disabled={bulkBusy}>
                Move to escalation
              </Button>
              <Button size="sm" variant="ghost" color="neutral" onClick={handleClearSelection} disabled={bulkBusy}>
                Clear
              </Button>
            </div>
          </Card>
        </div>
      ) : null}
    </div>
  );
}

export default CasesPage;
