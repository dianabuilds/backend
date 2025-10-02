import React from 'react';
import { ContentLayout } from '../ContentLayout';
import { Card, Input, Button, Checkbox, Select, Badge, Drawer, TablePagination } from "@ui";
import { apiGet, apiPost, apiDelete } from '../../../shared/api/client';

import { MagnifyingGlassIcon, PlusIcon, TrashIcon, ArrowsRightLeftIcon } from '@heroicons/react/24/outline';

type Tag = {
  id: string;
  slug?: string;
  name: string;
  usage_count?: number;
  aliases_count?: number;
  created_at?: string;
};

export type TagGroupSummary = {
  key: string;
  tag_count: number;
  usage_count: number;
  author_count: number;
};

const PAGE_SIZE_OPTIONS = [10, 20, 30, 40, 50, 100];
const DEFAULT_GROUP: TagGroupSummary = { key: 'all', tag_count: 0, usage_count: 0, author_count: 0 };

type TagsPageProps = {
  context?: 'legacy' | 'nodes' | 'quests' | 'ops';
  defaultGroupKey?: string;
  title?: string;
  description?: React.ReactNode;
  groupFilter?: (group: TagGroupSummary) => boolean;
};

export default function TagsPage({
  context = 'legacy',
  defaultGroupKey = 'all',
  title = 'Tag governance',
  description,
  groupFilter,
}: TagsPageProps) {
  const [items, setItems] = React.useState<Tag[]>([]);
  const [groups, setGroups] = React.useState<TagGroupSummary[]>([]);
  const [group, setGroup] = React.useState<string>(defaultGroupKey);
  const [q, setQ] = React.useState('');
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [hasNext, setHasNext] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const [createOpen, setCreateOpen] = React.useState(false);
  const [newSlug, setNewSlug] = React.useState('');
  const [newName, setNewName] = React.useState('');
  const [creating, setCreating] = React.useState(false);
  const [createError, setCreateError] = React.useState<string | null>(null);

  const [selected, setSelected] = React.useState<Set<string>>(new Set());
  const [mergeReason, setMergeReason] = React.useState('');
  const [mergeBusy, setMergeBusy] = React.useState(false);

  React.useEffect(() => {
    setGroup(defaultGroupKey);
  }, [defaultGroupKey]);

  const filteredGroups = React.useMemo(() => {
    if (!groupFilter) return groups;
    return groups.filter(groupFilter);
  }, [groups, groupFilter]);

  React.useEffect(() => {
    if (group === 'all') return;
    const available = filteredGroups.some((g) => g.key === group) || (!filteredGroups.length && groups.some((g) => g.key === group));
    if (!available) {
      const fallback = filteredGroups[0]?.key ?? groups[0]?.key ?? 'all';
      setGroup(fallback);
    }
  }, [group, filteredGroups, groups]);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (q.trim()) params.set('q', q.trim());
      params.set('limit', String(pageSize));
      params.set('offset', String((page - 1) * pageSize));
      if (group && group !== 'all') params.set('type_', group);
      const data = await apiGet<any>(`/v1/admin/tags/list?${params.toString()}`);
      if (Array.isArray(data)) {
        setItems(data);
        setHasNext(data.length === pageSize);
      } else if (Array.isArray(data?.items)) {
        setItems(data.items);
        setHasNext(data.items.length === pageSize);
      } else {
        setItems([]);
        setHasNext(false);
      }
    } catch (err: any) {
      setError(String(err?.message || err || 'Failed to load tags'));
      setItems([]);
      setHasNext(false);
    } finally {
      setLoading(false);
    }
  }, [q, page, pageSize, group]);

  const loadGroups = React.useCallback(async () => {
    try {
      const data = await apiGet<any>('/v1/admin/tags/groups');
      if (Array.isArray(data)) setGroups(data);
      else if (Array.isArray(data?.items)) setGroups(data.items);
    } catch (err) {
      console.warn('Failed to load tag groups', err);
    }
  }, []);

  React.useEffect(() => {
    const handle = setTimeout(() => {
      void load();
    }, 200);
    return () => clearTimeout(handle);
  }, [load]);

  React.useEffect(() => {
    void loadGroups();
  }, [loadGroups]);

  React.useEffect(() => {
    setSelected(new Set());
  }, [page, items]);

  const totals = React.useMemo(() => {
    const source = filteredGroups.length ? filteredGroups : groups;
    const sum = source.reduce(
      (acc, g) => {
        acc.tags += g.tag_count;
        acc.usage += g.usage_count;
        acc.authors += g.author_count;
        return acc;
      },
      { tags: 0, usage: 0, authors: 0 },
    );
    return sum;
  }, [filteredGroups, groups]);

  const headerStats = [
    { label: 'Tags', value: totals.tags.toLocaleString() },
    { label: 'Usage events', value: totals.usage.toLocaleString() },
    { label: 'Authors', value: totals.authors.toLocaleString() },
  ];

  const layoutDescription = description ?? 'Review usage across content types, consolidate synonyms, and grow controlled vocabulary.';

  const groupOptions: TagGroupSummary[] = React.useMemo(() => {
    const source = filteredGroups.length ? filteredGroups : groups;
    if (!source.length) return [DEFAULT_GROUP];
    return [
      { key: 'all', tag_count: totals.tags, usage_count: totals.usage, author_count: totals.authors },
      ...source,
    ];
  }, [filteredGroups, groups, totals]);

  const toggleSelectAll = (checked: boolean) => {
    if (checked) setSelected(new Set(items.map((item) => item.id)));
    else setSelected(new Set());
  };

  const toggleSelected = (id: string, checked: boolean) => {
    setSelected((prev) => {
      const draft = new Set(prev);
      if (checked) draft.add(id);
      else draft.delete(id);
      return draft;
    });
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this tag?')) return;
    try {
      await apiDelete(`/v1/admin/tags/${encodeURIComponent(id)}`);
      await load();
      await loadGroups();
    } catch (err: any) {
      alert(String(err?.message || err || 'Failed to delete tag'));
    }
  };

  const handleBulkDelete = async () => {
    if (selected.size === 0) return;
    if (!confirm(`Delete ${selected.size} selected tag(s)?`)) return;
    try {
      for (const id of Array.from(selected)) {
        await apiDelete(`/v1/admin/tags/${encodeURIComponent(id)}`);
      }
      setSelected(new Set());
      await load();
      await loadGroups();
    } catch (err: any) {
      alert(String(err?.message || err || 'Bulk delete failed'));
    }
  };

  const handleBulkMerge = async () => {
    const ids = Array.from(selected);
    if (ids.length < 2) return;
    const [target, ...sources] = ids;
    const targetTag = items.find((t) => t.id === target);
    const targetLabel = targetTag ? `#${targetTag.name}` : target;
    if (!confirm(`Merge ${sources.length} tag(s) into ${targetLabel}?`)) return;
    try {
      setMergeBusy(true);
      for (const from of sources) {
        await apiPost('/v1/admin/tags/merge', {
          from_id: from,
          to_id: target,
          dryRun: false,
          reason: mergeReason || undefined,
          type: group,
        });
      }
      setSelected(new Set([target]));
      setMergeReason('');
      await load();
      await loadGroups();
    } catch (err: any) {
      alert(String(err?.message || err || 'Merge failed'));
    } finally {
      setMergeBusy(false);
    }
  };

  const createTag = async () => {
    if (!newSlug.trim() || !newName.trim()) {
      setCreateError('Slug and name are required');
      return;
    }
    setCreating(true);
    setCreateError(null);
    try {
      await apiPost('/v1/admin/tags', { slug: newSlug.trim(), name: newName.trim() });
      setCreateOpen(false);
      setNewSlug('');
      setNewName('');
      await load();
      await loadGroups();
    } catch (err: any) {
      setCreateError(String(err?.message || err || 'Failed to create tag'));
    } finally {
      setCreating(false);
    }
  };

  const selectedCount = selected.size;


  return (
    <ContentLayout
      context={context}
      title={title}
      description={layoutDescription}
      stats={headerStats}
    >
      <Card className="p-4 space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[220px]">
            <MagnifyingGlassIcon className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
            <Input
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setPage(1);
              }}
              placeholder="Search tags..."
              className="pl-9"
            />
          </div>
          <Select
            value={String(pageSize)}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="h-10 w-28"
          >
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size} / page
              </option>
            ))}
          </Select>
          <Button onClick={() => setCreateOpen(true)}>
            <PlusIcon className="mr-2 h-4 w-4" /> New tag
          </Button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {groupOptions.map((g) => {
            const isActive = group === g.key;
            return (
              <button
                key={g.key}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
                  isActive
                    ? 'bg-primary-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-dark-700 dark:text-dark-100 dark:hover:bg-dark-650'
                }`}
                onClick={() => {
                  setGroup(g.key);
                  setPage(1);
                }}
              >
                <span className="capitalize">{g.key === 'all' ? 'All tags' : g.key}</span>
                <Badge color="neutral" variant="soft" className="ml-2">
                  {g.tag_count.toLocaleString()}
                </Badge>
              </button>
            );
          })}
        </div>

        {error && <div className="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

        <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-dark-600">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:bg-dark-800 dark:text-dark-300">
              <tr>
                <th className="px-4 py-3">
                  <Checkbox
                    checked={selectedCount > 0 && selectedCount === items.length}
                    onChange={(e: any) => toggleSelectAll(e.target.checked)}
                  />
                </th>
                <th className="px-4 py-3">Slug</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Usage</th>
                <th className="px-4 py-3">Aliases</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-dark-700">
              {items.map((tag) => {
                const checked = selected.has(tag.id);
                return (
                  <tr key={tag.id} className="bg-white/90 text-sm transition hover:bg-white dark:bg-dark-800/80 dark:hover:bg-dark-750">
                    <td className="px-4 py-3">
                      <Checkbox checked={checked} onChange={(e: any) => toggleSelected(tag.id, e.target.checked)} />
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500 dark:text-dark-200">{tag.slug}</td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">#{tag.name}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-dark-200">{(tag.usage_count ?? 0).toLocaleString()}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-dark-200">{tag.aliases_count ?? 0}</td>
                    <td className="px-4 py-3 text-xs text-gray-400 dark:text-dark-300">{tag.created_at ? new Date(tag.created_at).toLocaleDateString() : '—'}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" color="neutral" size="sm" onClick={() => handleDelete(tag.id)}>
                          <TrashIcon className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {!loading && items.length === 0 && (
                <tr>
                  <td className="px-4 py-6 text-center text-sm text-gray-500" colSpan={7}>
                    No tags in this group
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          {loading && (
            <div className="flex items-center justify-center py-6 text-sm text-gray-500">Loading tags…</div>
          )}
        </div>

        <TablePagination
          page={page}
          pageSize={pageSize}
          currentCount={items.length}
          hasNext={hasNext}
          onPageChange={(value) => setPage(value)}
          onPageSizeChange={(value) => { setPageSize(value); setPage(1); }}
          pageSizeOptions={PAGE_SIZE_OPTIONS}
        />
        {selectedCount > 0 && (
          <div className="rounded-lg border border-primary-200 bg-primary-50 p-4 text-sm dark:border-primary-700 dark:bg-primary-900/20">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-medium">Selected: {selectedCount}</span>
              <Button variant="outlined" color="neutral" onClick={() => setSelected(new Set())}>
                Clear selection
              </Button>
              <Button variant="outlined" color="neutral" onClick={() => setMergeReason('')} disabled={mergeBusy}>
                Reset merge note
              </Button>
              <Button color="neutral" variant="outlined" onClick={handleBulkDelete} disabled={mergeBusy}>
                <TrashIcon className="mr-2 h-4 w-4" /> Delete selected
              </Button>
              <Button onClick={handleBulkMerge} disabled={mergeBusy || selectedCount < 2}>
                <ArrowsRightLeftIcon className="mr-2 h-4 w-4" /> Merge into first
              </Button>
              <Input
                value={mergeReason}
                onChange={(e) => setMergeReason(e.target.value)}
                placeholder="Merge reason (optional)"
                className="min-w-[200px]"
              />
            </div>
          </div>
        )}
      </Card>

      <Drawer
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="Create tag"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outlined" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={createTag} disabled={creating}>
              {creating ? 'Creating…' : 'Create tag'}
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          {createError && <div className="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{createError}</div>}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Slug</label>
            <Input value={newSlug} onChange={(e) => setNewSlug(e.target.value)} placeholder="unique-slug" />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Name</label>
            <Input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Readable tag name" />
          </div>
        </div>
      </Drawer>
    </ContentLayout>
  );
}
