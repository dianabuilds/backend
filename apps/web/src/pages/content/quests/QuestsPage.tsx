import React from 'react';
import { useSearchParams } from 'react-router-dom';

import { ContentLayout } from '../ContentLayout';
import { Badge, Button, Card, Input, Select, Switch, Table, TablePagination, Textarea } from '@ui';
import { apiGet, apiPost } from '@shared/api/client';
import { usePaginatedQuery } from '@shared/hooks/usePaginatedQuery';
import { extractErrorMessage } from '@shared/utils/errors';
import { formatDateTime } from '@shared/utils/format';
import { translate } from '@shared/i18n/locale';
type QuestStatus = 'all' | 'draft' | 'published';

type Quest = {
  id: string;
  title: string;
  slug?: string | null;
  is_public?: boolean;
  status?: string | null;
  updated_at?: string | null;
};

type QuestListResponse = {
  items?: Quest[];
  total?: number;
  offset?: number;
  limit?: number;
  has_next?: boolean;
};

type QuestFetchResult = {
  items: Quest[];
  hasNext: boolean;
  total?: number;
  source: 'api' | 'fallback';
};

type QuestCreateResponse = {
  quest?: (Quest & { quest_id?: string | number }) | null;
  id?: string | number;
  quest_id?: string | number;
  slug?: string | null;
} & Partial<Quest>;

const STATUS_OPTIONS: Array<{ value: QuestStatus; label: string }> = [
  { value: 'all', label: 'All quests' },
  { value: 'draft', label: 'Draft' },
  { value: 'published', label: 'Published' },
];

const FALLBACK_QUESTS: Quest[] = Array.from({ length: 24 }, (_, index) => ({
  id: String(index + 1),
  title: `Sample quest ${index + 1}`,
  slug: `quest-${index + 1}`,
  is_public: index % 2 === 0,
  status: index % 2 === 0 ? 'published' : 'draft',
  updated_at: new Date(Date.now() - index * 36e5).toISOString(),
}));

const QUEST_TOASTS = {
  loadError: { en: 'Failed to load quests', ru: 'Не удалось загрузить квесты' },
};


function normalizeQuest(raw: any): Quest {
  return {
    id: raw?.id != null ? String(raw.id) : '',
    title: raw?.title ?? '',
    slug: raw?.slug ?? null,
    is_public: raw?.is_public === true,
    status: typeof raw?.status === 'string' ? raw.status : raw?.is_public ? 'published' : 'draft',
    updated_at: raw?.updated_at ?? raw?.updatedAt ?? null,
  };
}

function filterByStatus(list: Quest[], status: QuestStatus): Quest[] {
  if (status === 'all') return list;
  return list.filter((quest) => {
    const normalized = (quest.status ?? '').toLowerCase();
    if (status === 'published') {
      return normalized === 'published' || quest.is_public === true;
    }
    return normalized === 'draft' || quest.is_public === false;
  });
}

function formatStatusBadge(quest: Quest): { label: string; color: 'success' | 'warning' } {
  const normalized = (quest.status ?? '').toLowerCase();
  const published = normalized === 'published' || quest.is_public === true;
  return published ? { label: 'Published', color: 'success' } : { label: 'Draft', color: 'warning' };
}

function parseTags(input: string): string[] {
  return input
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean);
}

export default function QuestsPage(): React.ReactElement {
  const [params, setParams] = useSearchParams();
  const [status, setStatus] = React.useState<QuestStatus>('all');
  const [query, setQuery] = React.useState('');
  const [createOpen, setCreateOpen] = React.useState(params.get('create') === '1');
  const [title, setTitle] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [tags, setTags] = React.useState('');
  const [isPublic, setIsPublic] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [created, setCreated] = React.useState<{ id: string; slug?: string } | null>(null);
  const [dataSource, setDataSource] = React.useState<'api' | 'fallback'>('api');
  const [totalCount, setTotalCount] = React.useState<number | null>(null);

  const {
    items,
    page,
    setPage,
    pageSize,
    setPageSize,
    hasNext,
    loading,
    error,
    refresh,
  } = usePaginatedQuery<Quest, QuestFetchResult>({
    initialPageSize: 20,
    dependencies: [query, status],
    debounceMs: 250,
    fetcher: async ({ page: currentPage, pageSize: currentPageSize, signal }) => {
      const offset = (currentPage - 1) * currentPageSize;
      const params = new URLSearchParams({
        limit: String(currentPageSize),
        offset: String(offset),
      });
      const trimmedQuery = query.trim();
      if (trimmedQuery) params.set('q', trimmedQuery);
      if (status !== 'all') params.set('status', status);

      const endpoints = [`/v1/quests?${params.toString()}`, `/v1/admin/quests/list?${params.toString()}`];
      for (const url of endpoints) {
        try {
          const response = await apiGet<QuestListResponse | Quest[]>(url, { signal });
          if (!response) continue;
          const rows = Array.isArray(response)
            ? response.map(normalizeQuest)
            : Array.isArray(response?.items)
            ? response.items.map(normalizeQuest)
            : [];
          const filteredRows = filterByStatus(rows, status);
          const hasMore =
            typeof (response as QuestListResponse)?.has_next === 'boolean'
              ? Boolean((response as QuestListResponse).has_next)
              : filteredRows.length === currentPageSize;
          const total =
            typeof (response as QuestListResponse)?.total === 'number'
              ? (response as QuestListResponse).total
              : hasMore
              ? undefined
              : filteredRows.length + offset;
          return {
            items: filteredRows,
            hasNext: hasMore,
            total,
            source: 'api' as const,
          };
        } catch (err) {
          if (signal?.aborted) throw err;
        }
      }

      const base = filterByStatus(
        FALLBACK_QUESTS.filter((quest) => {
          if (!trimmedQuery) return true;
          const haystack = `${quest.title} ${quest.slug ?? ''}`.toLowerCase();
          return haystack.includes(trimmedQuery.toLowerCase());
        }),
        status,
      );
      const slice = base.slice(offset, offset + currentPageSize);
      return {
        items: slice,
        hasNext: offset + currentPageSize < base.length,
        total: base.length,
        source: 'fallback' as const,
      };
    },
    mapResponse: (payload) => {
      setDataSource(payload.source);
      setTotalCount(typeof payload.total === 'number' ? payload.total : null);
      return payload;
    },
    onError: (err) => extractErrorMessage(err, translate(QUEST_TOASTS.loadError)),
  });

  React.useEffect(() => {
    setCreateOpen(params.get('create') === '1');
  }, [params]);

  React.useEffect(() => {
    const preset = params.get('status');
    if (preset === 'all' || preset === 'draft' || preset === 'published') {
      if (preset !== status) {
        setStatus(preset);
        setPage(1);
      }
    }
  }, [params, status, setPage]);

  const handleQueryChange = React.useCallback(
    (value: string) => {
      setQuery(value);
      setPage(1);
    },
    [setPage],
  );

  const applyStatus = React.useCallback(
    (next: QuestStatus) => {
      setStatus(next);
      setPage(1);
      const nextParams = new URLSearchParams(params);
      if (next === 'all') nextParams.delete('status');
      else nextParams.set('status', next);
      setParams(nextParams, { replace: true });
    },
    [params, setParams, setPage],
  );

  const openCreate = React.useCallback(() => {
    setCreateOpen(true);
    const next = new URLSearchParams(params);
    next.set('create', '1');
    setParams(next, { replace: true });
  }, [params, setParams]);

  const closeCreate = React.useCallback(() => {
    setCreateOpen(false);
    const next = new URLSearchParams(params);
    next.delete('create');
    setParams(next, { replace: true });
  }, [params, setParams]);

  const createQuest = React.useCallback(async () => {
    setBusy(true);
    setFormError(null);
    setCreated(null);
    try {
      const payload = {
        title: title.trim(),
        description: description.trim() || undefined,
        tags: parseTags(tags),
        is_public: isPublic,
      };
      if (!payload.title) {
        setFormError('Title is required.');
        setBusy(false);
        return;
      }
      const response = await apiPost<QuestCreateResponse>('/v1/quests', payload);
      const createdQuest = response?.quest ?? response;
      if (!createdQuest) {
        throw new Error('Quest was not created');
      }
      setCreated({ id: String(createdQuest.id ?? createdQuest.quest_id ?? ''), slug: createdQuest.slug ?? undefined });
      setTitle('');
      setDescription('');
      setTags('');
      setIsPublic(false);
      await refresh();
    } catch (err) {
      const message = extractErrorMessage(err, 'Failed to create quest');
      setFormError(message);
    } finally {
      setBusy(false);
    }
  }, [description, isPublic, refresh, tags, title]);

  const rangeStart = items.length ? (page - 1) * pageSize + 1 : 0;
  const rangeEnd = (page - 1) * pageSize + items.length;

  return (
    <ContentLayout
      context="quests"
      title="Quest library"
      description="Search quests, publish new storylines, and keep draft work moving."
    >
      <Card className="space-y-4 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <Input
            value={query}
            onChange={(event) => handleQueryChange(event.target.value)}
            placeholder="Search by title or slug"
            className="w-full sm:w-64"
          />
          <Select
            value={status}
            onChange={(event) => applyStatus(event.target.value as QuestStatus)}
            className="w-full sm:w-48"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <div className="flex-1" />
          <Button onClick={openCreate}>New quest</Button>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500">
          <span>
            {items.length
              ? `Showing ${rangeStart.toLocaleString()} to ${rangeEnd.toLocaleString()}${
                  totalCount != null ? ` of ${totalCount.toLocaleString()}` : ''
                }`
              : 'No quests to display yet.'}
          </span>
          {dataSource === 'fallback' && (
            <span className="text-amber-600">Using cached fallback data until the API responds.</span>
          )}
        </div>
      </Card>

      {createOpen && (
        <Card className="mt-4 space-y-4 p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Create quest</h2>
            <Button variant="ghost" onClick={closeCreate}>
              Close
            </Button>
          </div>
          {formError && (
            <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {formError}
            </div>
          )}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2 md:col-span-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Title</label>
              <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Story arc title" />
            </div>
            <div className="space-y-2 md:col-span-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Description</label>
              <Textarea
                rows={3}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Short summary for collaborators"
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Tags (comma separated)</label>
              <Input value={tags} onChange={(event) => setTags(event.target.value)} placeholder="story, ai, demo" />
            </div>
            <div className="flex items-center gap-3 md:col-span-2">
              <Switch
                checked={isPublic}
                onChange={(event) => setIsPublic(event.currentTarget.checked)}
                label="Publish immediately"
              />
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={createQuest} disabled={busy}>
              {busy ? 'Creating...' : 'Create quest'}
            </Button>
            {created && (
              <span className="text-sm text-gray-600">
                Created quest {created.id}
                {created.slug ? ` (slug: ${created.slug})` : ''}
              </span>
            )}
          </div>
        </Card>
      )}

      <Card className="mt-4 space-y-4 p-4">
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </div>
        )}
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Quests</h2>
          <Button variant="ghost" onClick={() => void refresh()} disabled={loading}>
            Refresh
          </Button>
        </div>
        <div className="overflow-x-auto">
          <Table.Table className="min-w-[640px]">
            <Table.THead>
              <Table.TR>
                <Table.TH>Title</Table.TH>
                <Table.TH>Slug</Table.TH>
                <Table.TH>Status</Table.TH>
                <Table.TH>Updated</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {loading && items.length === 0 ? (
                <Table.TR>
                  <Table.TD colSpan={4} className="py-6 text-center text-sm text-gray-500">
                    Loading quests...
                  </Table.TD>
                </Table.TR>
              ) : null}
              {!loading && items.length === 0 ? (
                <Table.TR>
                  <Table.TD colSpan={4} className="py-6 text-center text-sm text-gray-500">
                    No quests found. Adjust filters or create a new quest.
                  </Table.TD>
                </Table.TR>
              ) : null}
              {items.map((quest) => {
                const statusBadge = formatStatusBadge(quest);
                return (
                  <Table.TR key={quest.id} className="text-sm">
                    <Table.TD className="py-3 font-medium text-gray-900">{quest.title || 'Untitled quest'}</Table.TD>
                    <Table.TD className="py-3 text-gray-600">{quest.slug || '--'}</Table.TD>
                    <Table.TD className="py-3">
                      <Badge color={statusBadge.color} variant="soft">
                        {statusBadge.label}
                      </Badge>
                    </Table.TD>
                    <Table.TD className="py-3 text-gray-500">{formatDateTime(quest.updated_at ?? undefined, { fallback: '--' })}</Table.TD>
                  </Table.TR>
                );
              })}
            </Table.TBody>
          </Table.Table>
        </div>
        <TablePagination
          page={page}
          pageSize={pageSize}
          currentCount={items.length}
          hasNext={hasNext}
          totalItems={totalCount ?? undefined}
          onPageChange={setPage}
          onPageSizeChange={(nextSize) => {
            setPageSize(nextSize);
            setPage(1);
          }}
        />
      </Card>
    </ContentLayout>
  );
}


