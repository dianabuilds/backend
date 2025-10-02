import React from 'react';
import { ContentLayout } from '../ContentLayout';
import { Card, Input, Button, Checkbox, Select, Badge, Drawer, TablePagination, useToast } from '@ui';
import { MagnifyingGlassIcon, PlusIcon, TrashIcon, ArrowsRightLeftIcon } from '@heroicons/react/24/outline';

import { apiGet, apiPost, apiDelete } from '../../../shared/api/client';
import { extractErrorMessage } from '../../../shared/utils/errors';
import { usePaginatedQuery } from '../../../shared/hooks/usePaginatedQuery';
import { useConfirmDialog } from '../../../shared/hooks/useConfirmDialog';
import { translate } from '../../../shared/i18n/locale';
import type { Locale } from '../../../shared/i18n/locale';

type Tag = {
  id: string;
  slug?: string | null;
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

type TagsPageProps = {
  context?: 'legacy' | 'nodes' | 'quests' | 'ops';
  defaultGroupKey?: string;
  title?: string;
  description?: React.ReactNode;
  groupFilter?: (group: TagGroupSummary) => boolean;
};

const PAGE_SIZE_OPTIONS = [10, 20, 30, 40, 50, 100];
const DEFAULT_GROUP: TagGroupSummary = { key: 'all', tag_count: 0, usage_count: 0, author_count: 0 };

const COPY = {
  pageTitle: { en: 'Tag governance', ru: 'Управление тегами' },
  searchPlaceholder: { en: 'Search by name or slug', ru: 'Поиск по названию или slug' },
  allTagsOption: { en: 'All tags', ru: 'Все теги' },
  listSuffix: { en: 'in the current list', ru: 'в текущем списке' },
  table: {
    name: { en: 'Name', ru: 'Название' },
    usage: { en: 'Usage', ru: 'Использования' },
    aliases: { en: 'Aliases', ru: 'Псевдонимы' },
    created: { en: 'Created', ru: 'Создан' },
    actions: { en: 'Actions', ru: 'Действия' },
  },
  messages: {
    loading: { en: 'Loading…', ru: 'Загрузка…' },
    empty: { en: 'No tags found.', ru: 'Теги не найдены.' },
    groupsLoadError: { en: 'Failed to load tag groups', ru: 'Не удалось загрузить группы тегов' },
    tagsLoadError: { en: 'Failed to load tags', ru: 'Не удалось загрузить теги' },
    createFormError: { en: 'Slug and name are required.', ru: 'Slug и имя обязательны.' },
    deleteError: { en: 'Failed to delete tag', ru: 'Не удалось удалить тег' },
    bulkDeleteError: { en: 'Failed to delete selected tags', ru: 'Не удалось удалить выбранные теги' },
    mergeError: { en: 'Failed to merge tags', ru: 'Не удалось объединить теги' },
    createError: { en: 'Failed to create tag', ru: 'Не удалось создать тег' },
  },
  toasts: {
    deleteSuccess: { en: 'Tag deleted.', ru: 'Тег удалён.' },
    bulkDeleteSuccess: { en: 'Selected tags deleted.', ru: 'Выбранные теги удалены.' },
    mergeSuccess: { en: 'Tags merged.', ru: 'Теги объединены.' },
    createSuccess: { en: 'Tag created.', ru: 'Тег создан.' },
  },
  selection: {
    selectedPrefix: { en: 'Selected', ru: 'Выбрано' },
    clearSelection: { en: 'Clear selection', ru: 'Очистить выбор' },
    resetComment: { en: 'Reset comment', ru: 'Сбросить комментарий' },
    deleteSelected: { en: 'Delete selected', ru: 'Удалить выбранные' },
    mergeIntoFirst: { en: 'Merge into first', ru: 'Объединить в первый' },
    mergeReasonPlaceholder: { en: 'Comment for merge (optional)', ru: 'Комментарий к объединению (необязательно)' },
  },
  drawer: {
    title: { en: 'Create tag', ru: 'Создать тег' },
    cancel: { en: 'Cancel', ru: 'Отмена' },
    submit: { en: 'Create tag', ru: 'Создать тег' },
    submitting: { en: 'Creating…', ru: 'Создание…' },
    slugLabel: { en: 'Slug', ru: 'Slug' },
    slugPlaceholder: { en: 'unique-slug', ru: 'уникальный-slug' },
    nameLabel: { en: 'Name', ru: 'Название' },
    namePlaceholder: { en: 'Readable tag name', ru: 'Читаемое название тега' },
  },
  stats: {
    tags: { en: 'Tags in group', ru: 'Теги в группе' },
    usage: { en: 'Usage count', ru: 'Использования' },
    authors: { en: 'Authors', ru: 'Авторы' },
  },
  confirm: {
    deleteTagTitle: { en: 'Delete tag', ru: 'Удалить тег' },
    deleteTagConfirm: { en: 'Delete', ru: 'Удалить' },
    cancel: { en: 'Cancel', ru: 'Отмена' },
    bulkDeleteTitle: { en: 'Delete selected tags', ru: 'Удалить выбранные теги' },
    bulkDeleteConfirm: { en: 'Delete', ru: 'Удалить' },
    mergeTitle: { en: 'Merge tags', ru: 'Объединить теги' },
    mergeConfirm: { en: 'Merge', ru: 'Объединить' },
  },
};

function tagLabelCopy(tag?: Tag | null): Record<Locale, string> {
  if (!tag) {
    return { en: 'this tag', ru: 'этот тег' };
  }
  if (tag.name) {
    return { en: `tag #${tag.name}`, ru: `тег #${tag.name}` };
  }
  if (tag.slug) {
    return { en: `tag ${tag.slug}`, ru: `тег ${tag.slug}` };
  }
  return { en: 'this tag', ru: 'этот тег' };
}



function toLocaleDate(value?: string): string {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

function normalizeTag(raw: any): Tag {
  return {
    id: raw?.id != null ? String(raw.id) : '',
    slug: raw?.slug != null ? String(raw.slug) : null,
    name: raw?.name != null ? String(raw.name) : '',
    usage_count: typeof raw?.usage_count === 'number' ? raw.usage_count : undefined,
    aliases_count: typeof raw?.aliases_count === 'number' ? raw.aliases_count : undefined,
    created_at: typeof raw?.created_at === 'string' ? raw.created_at : undefined,
  };
}

export default function TagsPage({
  context = 'legacy',
  defaultGroupKey = 'all',
  title,
  description,
  groupFilter,
}: TagsPageProps) {
  const { pushToast } = useToast();
  const resolvedTitle = title ?? translate(COPY.pageTitle);

  const [groups, setGroups] = React.useState<TagGroupSummary[]>([]);
  const [group, setGroup] = React.useState<string>(defaultGroupKey);
  const [q, setQ] = React.useState('');

  const [createOpen, setCreateOpen] = React.useState(false);
  const [newSlug, setNewSlug] = React.useState('');
  const [newName, setNewName] = React.useState('');
  const [creating, setCreating] = React.useState(false);
  const [createError, setCreateError] = React.useState<string | null>(null);

  const [selected, setSelected] = React.useState<Set<string>>(new Set());
  const [mergeReason, setMergeReason] = React.useState('');
  const [mergeBusy, setMergeBusy] = React.useState(false);

  const { confirm, confirmationElement } = useConfirmDialog();

  const {
    items,
    setItems,
    page,
    setPage,
    pageSize,
    setPageSize,
    hasNext,
    loading,
    error,
    setError,
    refresh,
  } = usePaginatedQuery<Tag, { items: Tag[]; hasNext: boolean }>({
    initialPageSize: 20,
    dependencies: [q, group],
    onError: (err) => extractErrorMessage(err, translate(COPY.messages.tagsLoadError)),
    fetcher: async ({ page: currentPage, pageSize: currentPageSize, signal }) => {
      const params = new URLSearchParams();
      if (q.trim()) params.set('q', q.trim());
      params.set('limit', String(currentPageSize));
      params.set('offset', String((currentPage - 1) * currentPageSize));
      if (group && group !== 'all') params.set('type_', group);
      const response = await apiGet<any>(`/v1/admin/tags/list?${params.toString()}`, { signal });
      const rawItems = Array.isArray(response)
        ? response
        : Array.isArray(response?.items)
        ? response.items
        : [];
      const normalized = rawItems.map(normalizeTag);
      return { items: normalized, hasNext: normalized.length === currentPageSize };
    },
    mapResponse: (data) => data,
  });

  React.useEffect(() => {
    setGroup(defaultGroupKey);
  }, [defaultGroupKey]);

  const filteredGroups = React.useMemo(() => {
    if (!groupFilter) return groups;
    return groups.filter(groupFilter);
  }, [groups, groupFilter]);

  React.useEffect(() => {
    if (group === 'all') return;
    const available =
      filteredGroups.some((entry) => entry.key === group) || (!filteredGroups.length && groups.some((entry) => entry.key === group));
    if (!available) {
      const fallback = filteredGroups[0]?.key ?? groups[0]?.key ?? 'all';
      setGroup(fallback);
      setPage(1);
    }
  }, [filteredGroups, group, groups, setPage]);

  React.useEffect(() => {
    const controller = new AbortController();
    (async () => {
      try {
        const data = await apiGet<any>('/v1/admin/tags/groups', { signal: controller.signal });
        if (Array.isArray(data)) setGroups(data);
        else if (Array.isArray(data?.items)) setGroups(data.items);
        else setGroups([]);
      } catch (err) {
        if ((err as any)?.name === 'AbortError') return;
        const message = extractErrorMessage(err, translate(COPY.messages.groupsLoadError));
        pushToast({ intent: 'error', description: message });
      }
    })();
    return () => controller.abort();
  }, [pushToast]);

  React.useEffect(() => {
    if (!error) return;
    pushToast({ intent: 'error', description: error });
    setError(null);
  }, [error, pushToast, setError]);

  React.useEffect(() => {
    setSelected(new Set());
  }, [group, q, page, items]);

  const selectedCount = selected.size;

  const toggleSelected = React.useCallback((id: string, checked: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  }, []);

  const toggleSelectAll = React.useCallback(
    (checked: boolean) => {
      if (checked) {
        setSelected(new Set(items.map((tag) => tag.id)));
      } else {
        setSelected(new Set());
      }
    },
    [items],
  );

  const handleDelete = React.useCallback(
    async (id: string) => {
      const tag = items.find((item) => item.id === id) || null;
      const labelCopy = tagLabelCopy(tag);
      const confirmed = await confirm({
        title: translate(COPY.confirm.deleteTagTitle),
        description: translate({
          en: `Delete ${labelCopy.en}? This action cannot be undone.`,
          ru: `Удалить ${labelCopy.ru}? Это действие нельзя отменить.`,
        }),
        confirmLabel: translate(COPY.confirm.deleteTagConfirm),
        cancelLabel: translate(COPY.confirm.cancel),
        destructive: true,
      });
      if (!confirmed) return;
      try {
        await apiDelete(`/v1/admin/tags/${encodeURIComponent(id)}`);
        setItems((prev) => prev.filter((item) => item.id !== id));
        setSelected((prev) => {
          const next = new Set(prev);
          next.delete(id);
          return next;
        });
        pushToast({ intent: 'success', description: translate(COPY.toasts.deleteSuccess) });
        void refresh();
      } catch (err) {
        const message = extractErrorMessage(err, translate(COPY.messages.deleteError));
        pushToast({ intent: 'error', description: message });
      }
    },
    [confirm, items, pushToast, refresh, setItems],
  );

  const handleBulkDelete = React.useCallback(async () => {
    if (selected.size === 0) return;
    const confirmed = await confirm({
      title: translate(COPY.confirm.bulkDeleteTitle),
      description: translate({
        en: `Delete ${selected.size} selected tag(s)? This action cannot be undone.`,
        ru: `Удалить ${selected.size} выбранные теги? Это действие нельзя отменить.`,
      }),
      confirmLabel: translate(COPY.confirm.bulkDeleteConfirm),
      cancelLabel: translate(COPY.confirm.cancel),
      destructive: true,
    });
    if (!confirmed) return;
    setMergeBusy(true);
    try {
      const ids = Array.from(selected);
      await Promise.all(ids.map((tagId) => apiDelete(`/v1/admin/tags/${encodeURIComponent(tagId)}`)));
      setItems((prev) => prev.filter((tag) => !selected.has(tag.id)));
      setSelected(new Set());
      pushToast({ intent: 'success', description: translate(COPY.toasts.bulkDeleteSuccess) });
      void refresh();
    } catch (err) {
      const message = extractErrorMessage(err, translate(COPY.messages.bulkDeleteError));
      pushToast({ intent: 'error', description: message });
    } finally {
      setMergeBusy(false);
    }
  }, [confirm, pushToast, refresh, selected, setItems]);

  const handleBulkMerge = React.useCallback(async () => {
    if (selected.size < 2) return;
    const ids = Array.from(selected);
    const target = ids[0];
    const sources = ids.slice(1);
    const targetTag = items.find((tag) => tag.id === target) || null;
    const labelCopy = tagLabelCopy(targetTag);
    const confirmed = await confirm({
      title: translate(COPY.confirm.mergeTitle),
      description: translate({
        en: `Merge ${sources.length} tag(s) into ${labelCopy.en}?`,
        ru: `Объединить ${sources.length} тегов в ${labelCopy.ru}?`,
      }),
      confirmLabel: translate(COPY.confirm.mergeConfirm),
      cancelLabel: translate(COPY.confirm.cancel),
    });
    if (!confirmed) return;
    setMergeBusy(true);
    try {
      await apiPost('/v1/admin/tags/merge', {
        target,
        sources,
        reason: mergeReason.trim() || undefined,
      });
      pushToast({ intent: 'success', description: translate(COPY.toasts.mergeSuccess) });
      setMergeReason('');
      setSelected(new Set([target]));
      void refresh();
    } catch (err) {
      const message = extractErrorMessage(err, translate(COPY.messages.mergeError));
      pushToast({ intent: 'error', description: message });
    } finally {
      setMergeBusy(false);
    }
  }, [confirm, items, mergeReason, pushToast, refresh, selected]);

  const createTag = React.useCallback(async () => {
    const slug = newSlug.trim();
    const name = newName.trim();
    if (!slug || !name) {
      setCreateError(translate(COPY.messages.createFormError));
      return;
    }
    setCreating(true);
    setCreateError(null);
    try {
      await apiPost('/v1/admin/tags', { slug, name });
      setCreateOpen(false);
      setNewSlug('');
      setNewName('');
      pushToast({ intent: 'success', description: translate(COPY.toasts.createSuccess) });
      void refresh();
    } catch (err) {
      const message = extractErrorMessage(err, translate(COPY.messages.createError));
      setCreateError(message);
      pushToast({ intent: 'error', description: message });
    } finally {
      setCreating(false);
    }
  }, [newName, newSlug, pushToast, refresh]);

  const stats = React.useMemo(() => {
    if (group === 'all') return undefined;
    const summary = groups.find((item) => item.key === group) ?? DEFAULT_GROUP;
    return [
      { label: translate(COPY.stats.tags), value: summary.tag_count.toLocaleString() },
      { label: translate(COPY.stats.usage), value: summary.usage_count.toLocaleString() },
      { label: translate(COPY.stats.authors), value: summary.author_count.toLocaleString() },
    ];
  }, [group, groups]);

  return (
    <>
      <ContentLayout
        context={context}
        title={resolvedTitle}
        description={description}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={() => setCreateOpen(true)}>
              <PlusIcon className="h-4 w-4" />
              <span className="ml-2">{translate(COPY.drawer.title)}</span>
            </Button>
          </div>
        }
        stats={stats}
      >
        <Card className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative w-full max-w-sm">
              <Input
                value={q}
                onChange={(event) => {
                  setQ(event.target.value);
                  setPage(1);
                }}
                placeholder={translate(COPY.searchPlaceholder)}
                prefix={<MagnifyingGlassIcon className="h-4 w-4" />}
              />
            </div>
            <Select
              value={group}
              onChange={(event) => {
                setGroup(event.target.value);
                setPage(1);
              }}
              className="min-w-[200px]"
            >
              {[DEFAULT_GROUP, ...filteredGroups].map((entry) => (
                <option key={entry.key} value={entry.key}>
                  {entry.key === 'all' ? translate(COPY.allTagsOption) : entry.key}
                </option>
              ))}
            </Select>
            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
              <Badge color="neutral">{items.length}</Badge>
              <span>{translate(COPY.listSuffix)}</span>
            </div>
          </div>

          <div className="mt-4 overflow-x-auto rounded-xl border border-gray-200 dark:border-dark-600">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:bg-dark-800 dark:text-dark-300">
                <tr>
                  <th className="px-4 py-3">
                    <Checkbox
                      checked={selectedCount > 0 && selectedCount === items.length}
                      onChange={(event: any) => toggleSelectAll(event.target.checked)}
                      aria-label={translate({ en: 'Select all', ru: 'Выбрать все' })}
                    />
                  </th>
                  <th className="px-4 py-3">Slug</th>
                  <th className="px-4 py-3">{translate(COPY.table.name)}</th>
                  <th className="px-4 py-3">{translate(COPY.table.usage)}</th>
                  <th className="px-4 py-3">{translate(COPY.table.aliases)}</th>
                  <th className="px-4 py-3">{translate(COPY.table.created)}</th>
                  <th className="px-4 py-3 text-right">{translate(COPY.table.actions)}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-dark-700">
                {items.map((tag) => {
                  const checked = selected.has(tag.id);
                  const labelCopy = tagLabelCopy(tag);
                  const selectLabel = translate({ en: `Select ${labelCopy.en}`, ru: `Выбрать ${labelCopy.ru}` });
                  const deleteLabel = translate({ en: `Delete ${labelCopy.en}`, ru: `Удалить ${labelCopy.ru}` });
                  return (
                    <tr key={tag.id} className="bg-white/90 text-sm transition hover:bg-white dark:bg-dark-800/80 dark:hover:bg-dark-750">
                      <td className="px-4 py-3">
                        <Checkbox
                          checked={checked}
                          onChange={(event: any) => toggleSelected(tag.id, event.target.checked)}
                          aria-label={selectLabel}
                        />
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-500 dark:text-dark-200">{tag.slug || '—'}</td>
                      <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">#{tag.name}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-dark-200">{(tag.usage_count ?? 0).toLocaleString()}</td>
                      <td className="px-4 py-3 text-gray-600 dark:text-dark-200">{tag.aliases_count ?? 0}</td>
                      <td className="px-4 py-3 text-xs text-gray-400 dark:text-dark-300">{toLocaleDate(tag.created_at)}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            color="neutral"
                            size="sm"
                            onClick={() => handleDelete(tag.id)}
                            aria-label={deleteLabel}
                          >
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
                      {translate(COPY.messages.empty)}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            {loading && (
              <div className="flex items-center justify-center py-6 text-sm text-gray-500">{translate(COPY.messages.loading)}</div>
            )}
          </div>

          <TablePagination
            page={page}
            pageSize={pageSize}
            currentCount={items.length}
            hasNext={hasNext}
            onPageChange={(nextPage: number) => setPage(nextPage)}
            onPageSizeChange={(size) => setPageSize(size)}
            pageSizeOptions={PAGE_SIZE_OPTIONS}
          />

          {selectedCount > 0 && (
            <div className="mt-4 rounded-lg border border-primary-200 bg-primary-50 p-4 text-sm dark:border-primary-700 dark:bg-primary-900/20">
              <div className="flex flex-wrap items-center gap-3">
                <span className="font-medium">
                  {translate(COPY.selection.selectedPrefix)}: {selectedCount}
                </span>
                <Button variant="outlined" color="neutral" onClick={() => setSelected(new Set())}>
                  {translate(COPY.selection.clearSelection)}
                </Button>
                <Button variant="outlined" color="neutral" onClick={() => setMergeReason('')} disabled={mergeBusy}>
                  {translate(COPY.selection.resetComment)}
                </Button>
                <Button color="neutral" variant="outlined" onClick={handleBulkDelete} disabled={mergeBusy}>
                  <TrashIcon className="mr-2 h-4 w-4" /> {translate(COPY.selection.deleteSelected)}
                </Button>
                <Button onClick={handleBulkMerge} disabled={mergeBusy || selectedCount < 2}>
                  <ArrowsRightLeftIcon className="mr-2 h-4 w-4" /> {translate(COPY.selection.mergeIntoFirst)}
                </Button>
                <Input
                  value={mergeReason}
                  onChange={(event) => setMergeReason(event.target.value)}
                  placeholder={translate(COPY.selection.mergeReasonPlaceholder)}
                  className="min-w-[220px]"
                />
              </div>
            </div>
          )}
        </Card>
      </ContentLayout>

      <Drawer
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title={translate(COPY.drawer.title)}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outlined" onClick={() => setCreateOpen(false)}>
              {translate(COPY.drawer.cancel)}
            </Button>
            <Button onClick={createTag} disabled={creating}>
              {creating ? translate(COPY.drawer.submitting) : translate(COPY.drawer.submit)}
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          {createError && (
            <div className="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-100">
              {createError}
            </div>
          )}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
              {translate(COPY.drawer.slugLabel)}
            </label>
            <Input value={newSlug} onChange={(event) => setNewSlug(event.target.value)} placeholder={translate(COPY.drawer.slugPlaceholder)} />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
              {translate(COPY.drawer.nameLabel)}
            </label>
            <Input value={newName} onChange={(event) => setNewName(event.target.value)} placeholder={translate(COPY.drawer.namePlaceholder)} />
          </div>
        </div>
      </Drawer>

      {confirmationElement}
    </>
  );
}
