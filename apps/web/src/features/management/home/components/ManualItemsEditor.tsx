import React from 'react';
import { Button, Dialog, Input, Spinner, Checkbox, TagInput } from '@ui';
import { extractErrorMessage } from '@shared/utils/errors';
import { fetchNodesList } from '@shared/api/nodes';
import { DEV_BLOG_TAG, type NodeItem } from '@shared/types/nodes';
import type { HomeBlockDataSourceEntity } from '../types';
import { DevBlogPostPicker } from './DevBlogPostPicker';

type ManualItemsEditorProps = {
  entity?: HomeBlockDataSourceEntity | null;
  items: string[];
  onChange: (items: string[]) => void;
  disabled?: boolean;
  error?: string;
};

type ManualPreviewEntry = {
  ref: string;
  title: string;
  subtitle: string | null;
  missing: boolean;
};

type ManualPreviewState = {
  loading: boolean;
  entries: ManualPreviewEntry[];
  error: string | null;
};

type NodePickerDialogProps = {
  open: boolean;
  entity: 'node' | 'quest';
  selected: string[];
  onClose: () => void;
  onSubmit: (items: string[]) => void;
};

const SUPPORTED_ENTITIES: ReadonlySet<HomeBlockDataSourceEntity> = new Set([
  'node',
  'quest',
  'dev_blog',
]);

const PICKER_LABELS: Record<'node' | 'quest' | 'dev_blog', string> = {
  node: 'материалы',
  quest: 'квесты',
  dev_blog: 'посты дев-блога',
};

const DEFAULT_PREVIEW: ManualPreviewState = {
  loading: false,
  entries: [],
  error: null,
};

function resolveEntityLabel(entity: HomeBlockDataSourceEntity | null | undefined): string {
  if (entity === 'node') return PICKER_LABELS.node;
  if (entity === 'quest') return PICKER_LABELS.quest;
  if (entity === 'dev_blog') return PICKER_LABELS.dev_blog;
  return 'элементы';
}

function normalizeItems(values: Array<string | number>): string[] {
  return values
    .map((value) => String(value).trim())
    .filter((value) => value.length > 0);
}

function uniqueSequence(values: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  values.forEach((value) => {
    if (!seen.has(value)) {
      seen.add(value);
      result.push(value);
    }
  });
  return result;
}

async function fetchNodePreview(ref: string, signal?: AbortSignal): Promise<ManualPreviewEntry> {
  const baseFallback: ManualPreviewEntry = {
    ref,
    title: ref,
    subtitle: null,
    missing: true,
  };
  try {
    const response = await fetchNodesList({ slug: ref, limit: 1, signal });
    let item = response.items[0];
    if (!item) {
      const fallback = await fetchNodesList({ q: ref, limit: 1, signal });
      item = fallback.items[0];
    }
    if (!item) {
      return baseFallback;
    }
    return normalizeNodeItem(ref, item);
  } catch (error: unknown) {
    if (signal?.aborted) {
      return baseFallback;
    }
    throw error;
  }
}

async function fetchDevBlogPreview(ref: string, signal?: AbortSignal): Promise<ManualPreviewEntry> {
  const baseFallback: ManualPreviewEntry = {
    ref,
    title: ref,
    subtitle: null,
    missing: true,
  };
  try {
    const response = await fetchNodesList({
      slug: ref,
      tag: DEV_BLOG_TAG,
      limit: 1,
      signal,
    });
    let item = response.items[0];
    if (!item) {
      const fallback = await fetchNodesList({
        q: ref,
        tag: DEV_BLOG_TAG,
        limit: 1,
        signal,
      });
      item = fallback.items[0];
    }
    if (!item) {
      return baseFallback;
    }
    return normalizeNodeItem(ref, item);
  } catch (error: unknown) {
    if (signal?.aborted) {
      return baseFallback;
    }
    throw error;
  }
}

function normalizeNodeItem(ref: string, item: NodeItem): ManualPreviewEntry {
  const title = item.title?.trim?.();
  const slug = item.slug?.trim?.();
  const id = item.id?.trim?.();
  const primary = title?.length ? title : slug?.length ? slug : id ?? ref;
  const subtitle = slug?.length ? slug : id?.length ? id : null;
  return {
    ref,
    title: primary,
    subtitle,
    missing: false,
  };
}

function useManualItemsPreview(entity: HomeBlockDataSourceEntity | null | undefined, refs: string[]): ManualPreviewState {
  const cacheRef = React.useRef<Map<string, ManualPreviewEntry>>(new Map());
  const previousKeyRef = React.useRef<string>('');
  const [state, setState] = React.useState<ManualPreviewState>(DEFAULT_PREVIEW);

  React.useEffect(() => {
    const normalizedRefs = normalizeItems(refs);
    const cacheKey = `${entity ?? 'none'}::${normalizedRefs.join('|')}`;
    if (previousKeyRef.current === cacheKey) {
      return;
    }
    previousKeyRef.current = cacheKey;

    if (!entity || normalizedRefs.length === 0) {
      setState(DEFAULT_PREVIEW);
      return;
    }

    const cache = cacheRef.current;
    const entries = normalizedRefs.map((ref) => cache.get(`${entity}:${ref}`) ?? {
      ref,
      title: ref,
      subtitle: null,
      missing: true,
    });
    const missingRefs = normalizedRefs.filter((ref) => !cache.has(`${entity}:${ref}`) || cache.get(`${entity}:${ref}`)?.missing);

    if (missingRefs.length === 0) {
      setState({
        loading: false,
        entries,
        error: null,
      });
      return;
    }

    let cancelled = false;
    const controller = new AbortController();
    setState({
      loading: true,
      entries,
      error: null,
    });

    const fetcher = entity === 'dev_blog' ? fetchDevBlogPreview : fetchNodePreview;

    (async () => {
      const previews: ManualPreviewEntry[] = [];
      for (const ref of missingRefs) {
        try {
          const preview = await fetcher(ref, controller.signal);
          previews.push(preview);
        } catch (error) {
          if (controller.signal.aborted) {
            return;
          }
          setState((current) => ({
            loading: false,
            entries: current.entries,
            error: extractErrorMessage(error, 'Не удалось загрузить данные об элементах.'),
          }));
          return;
        }
      }
      previews.forEach((entry) => {
        cache.set(`${entity}:${entry.ref}`, entry);
      });
      if (cancelled) {
        return;
      }
      setState({
        loading: false,
        entries: normalizedRefs.map((ref) => cache.get(`${entity}:${ref}`) ?? {
          ref,
          title: ref,
          subtitle: null,
          missing: true,
        }),
        error: null,
      });
    })();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [entity, refs]);

  return state;
}

function applySelection(current: string[], selected: string[]): string[] {
  const normalizedCurrent = normalizeItems(current);
  const normalizedSelected = uniqueSequence(selected);
  const preserved = normalizedCurrent.filter((ref) => normalizedSelected.includes(ref));
  const additions = normalizedSelected.filter((ref) => !preserved.includes(ref));
  return preserved.concat(additions);
}

export function ManualItemsEditor({
  entity,
  items,
  onChange,
  disabled = false,
  error,
}: ManualItemsEditorProps): React.ReactElement {
  const normalizedItems = React.useMemo(() => normalizeItems(items), [items]);
  const supported = entity ? SUPPORTED_ENTITIES.has(entity) : false;
  const [nodePickerOpen, setNodePickerOpen] = React.useState(false);
  const [devBlogPickerOpen, setDevBlogPickerOpen] = React.useState(false);

  const preview = useManualItemsPreview(entity ?? null, supported ? normalizedItems : []);

  const handleRemove = React.useCallback(
    (ref: string) => {
      if (disabled) return;
      onChange(normalizedItems.filter((item) => item !== ref));
    },
    [disabled, normalizedItems, onChange],
  );

  const handleMove = React.useCallback(
    (index: number, direction: -1 | 1) => {
      if (disabled) return;
      const nextIndex = index + direction;
      if (nextIndex < 0 || nextIndex >= normalizedItems.length) {
        return;
      }
      const next = [...normalizedItems];
      const [moved] = next.splice(index, 1);
      next.splice(nextIndex, 0, moved);
      onChange(next);
    },
    [disabled, normalizedItems, onChange],
  );

  const handleClear = React.useCallback(() => {
    if (disabled) return;
    onChange([]);
  }, [disabled, onChange]);

  const openPicker = React.useCallback(() => {
    if (!supported || disabled) return;
    if (entity === 'dev_blog') {
      setDevBlogPickerOpen(true);
    } else if (entity === 'node' || entity === 'quest') {
      setNodePickerOpen(true);
    }
  }, [disabled, entity, supported]);

  const handlePickerSubmit = React.useCallback(
    (selectedItems: string[]) => {
      const next = applySelection(normalizedItems, selectedItems);
      onChange(next);
    },
    [normalizedItems, onChange],
  );

  if (!supported) {
    return (
      <div className="space-y-2">
        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
          Для выбранного источника нет быстрого выбора. Введите идентификаторы вручную.
        </div>
        <TagInput
          label="Идентификаторы элементов"
          value={normalizedItems}
          onChange={(next) => onChange(uniqueSequence(next))}
          placeholder="например, node-42"
          disabled={disabled}
        />
        {error ? <div className="text-xs text-error">{error}</div> : null}
      </div>
    );
  }

  const label = resolveEntityLabel(entity);
  const missingWarnings = preview.entries.filter((entry) => entry.missing).length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <span className="text-sm font-semibold text-gray-900">Выбранные {label}</span>
          <p className="text-xs text-gray-500">Добавьте до 24 элементов в блок и отсортируйте их.</p>
        </div>
        <div className="flex items-center gap-2">
          {normalizedItems.length ? (
            <Button size="sm" variant="ghost" onClick={handleClear} disabled={disabled}>
              Очистить
            </Button>
          ) : null}
          <Button size="sm" onClick={openPicker} disabled={disabled}>
            {normalizedItems.length ? 'Изменить' : 'Добавить'}
          </Button>
        </div>
      </div>

      {preview.loading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Spinner size="sm" />
          <span>Загружаем данные…</span>
        </div>
      ) : null}

      {preview.entries.length === 0 && !preview.loading ? (
        <div className="rounded-lg border border-dashed border-gray-200 bg-gray-50 p-4 text-sm text-gray-500">
          Пока нет выбранных элементов.
        </div>
      ) : null}

      {preview.entries.length > 0 ? (
        <ol className="space-y-2">
          {preview.entries.map((entry, index) => (
            <li
              key={`${entry.ref}-${index}`}
              className="flex items-center justify-between gap-3 rounded-md border border-gray-200 bg-white px-3 py-2"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{entry.title}</span>
                  {entry.missing ? (
                    <span className="rounded-full bg-amber-100 px-2 py-[2px] text-xs font-medium text-amber-700">
                      не найден
                    </span>
                  ) : null}
                </div>
                <div className="text-xs text-gray-500">
                  {entry.subtitle ?? entry.ref}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={disabled || index === 0}
                  onClick={() => handleMove(index, -1)}
                >
                  Вверх
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={disabled || index === preview.entries.length - 1}
                  onClick={() => handleMove(index, 1)}
                >
                  Вниз
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  color="neutral"
                  disabled={disabled}
                  onClick={() => handleRemove(entry.ref)}
                >
                  Удалить
                </Button>
              </div>
            </li>
          ))}
        </ol>
      ) : null}

      {error ? <div className="text-xs text-error">{error}</div> : null}
      {!error && missingWarnings > 0 ? (
        <div className="text-xs text-amber-600">
          {missingWarnings} {missingWarnings === 1 ? 'элемент не найден и не появится в блоке.' : 'элемента не найдены и не появятся в блоке.'}
        </div>
      ) : null}
      {preview.error ? (
        <div className="text-xs text-amber-600">
          {preview.error}
        </div>
      ) : null}

      <DevBlogPostPicker
        open={devBlogPickerOpen && entity === 'dev_blog'}
        selected={normalizedItems}
        onClose={() => setDevBlogPickerOpen(false)}
        onSubmit={(ids) => {
          handlePickerSubmit(ids);
          setDevBlogPickerOpen(false);
        }}
      />

      <NodePickerDialog
        open={nodePickerOpen && (entity === 'node' || entity === 'quest')}
        entity={entity === 'quest' ? 'quest' : 'node'}
        selected={normalizedItems}
        onClose={() => setNodePickerOpen(false)}
        onSubmit={(ids) => {
          handlePickerSubmit(ids);
          setNodePickerOpen(false);
        }}
      />
    </div>
  );
}
function NodePickerDialog({
  open,
  entity,
  selected,
  onClose,
  onSubmit,
}: NodePickerDialogProps): React.ReactElement | null {
  const [query, setQuery] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [items, setItems] = React.useState<NodeItem[]>([]);
  const [selectedIds, setSelectedIds] = React.useState<Set<string>>(new Set(selected));

  React.useEffect(() => {
    if (!open) return;
    setQuery('');
    setSelectedIds(new Set(selected));
  }, [open, selected]);

  React.useEffect(() => {
    if (!open) return;
    let cancelled = false;
    const controller = new AbortController();
    const timeout = window.setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchNodesList({
          q: query.trim() || undefined,
          limit: 25,
          status: 'all',
          signal: controller.signal,
        });
        if (!cancelled) {
          setItems(response.items);
        }
      } catch (err) {
        if (!cancelled && !controller.signal.aborted) {
          setError(extractErrorMessage(err, 'Не удалось загрузить список материалов.'));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }, 250);

    return () => {
      cancelled = true;
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, [open, query, entity]);

  if (!open) {
    return null;
  }

  const toggleSelection = (id: string, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  };

  const submitSelection = () => {
    onSubmit(Array.from(selectedIds));
    onClose();
  };

  const label = PICKER_LABELS[entity] ?? 'элементы';

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={`Выбор элементов · ${label}`}
      size="lg"
      footer={(
        <>
          <Button variant="ghost" onClick={onClose}>
            Отмена
          </Button>
          <Button onClick={submitSelection} disabled={!selectedIds.size}>
            Применить ({selectedIds.size})
          </Button>
        </>
      )}
    >
      <div className="space-y-4">
        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={`Поиск ${label}…`}
        />
        {error ? (
          <div className="rounded border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </div>
        ) : null}
        <div className="max-h-80 overflow-y-auto rounded-md border border-gray-200">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner />
            </div>
          ) : items.length === 0 ? (
            <div className="py-12 text-center text-sm text-gray-500">
              Ничего не найдено для текущего запроса.
            </div>
          ) : (
            items.map((item) => {
              const ref = item.slug?.trim?.() || item.id || '';
              if (!ref) return null;
              const checked = selectedIds.has(ref);
              return (
                <div
                  key={ref}
                  className={`flex items-center justify-between gap-4 border-b border-gray-200 px-4 py-3 last:border-b-0 ${checked ? 'bg-primary-50/70' : ''}`}
                >
                  <div className="min-w-0">
                    <div className="truncate font-medium text-gray-900">
                      {item.title?.trim?.() || ref}
                    </div>
                    <div className="truncate text-xs text-gray-500">
                      {item.slug ?? item.id ?? '—'}
                    </div>
                  </div>
                  <Checkbox
                    checked={checked}
                    onChange={(event) => toggleSelection(ref, event.currentTarget.checked)}
                    aria-label={item.title ?? ref}
                  />
                </div>
              );
            })
          )}
        </div>
      </div>
    </Dialog>
  );
}
