import React from 'react';
import { Button, Dialog, Input, Checkbox, Spinner } from '@ui';
import { extractErrorMessage } from '@shared/utils/errors';
import { translate, translateWithVars } from '@shared/i18n/locale';
import { fetchNodesList } from '@shared/api/nodes';
import { DEV_BLOG_TAG, type NodeItem } from '@shared/types/nodes';

type DevBlogPostPickerProps = {
  open: boolean;
  selected: string[];
  onClose: () => void;
  onSubmit: (ids: string[]) => void;
};

const EMPTY_RESULT_TEXT = {
  en: 'No posts found for the current query.',
  ru: 'По запросу посты не найдены.',
};

const LOAD_ERROR_TEXT = {
  en: 'Failed to load posts. Please try again.',
  ru: 'Не удалось загрузить посты. Попробуйте ещё раз.',
};

const UNTITLED_POST_TEXT = {
  en: 'Untitled post',
  ru: 'Пост без названия',
};

const SEARCH_PLACEHOLDER = {
  en: 'Search by title or slug…',
  ru: 'Поиск по названию или слагу…',
};

const SELECTED_COUNT_TEXT = {
  en: '{{count}} post(s) selected',
  ru: 'Выбрано постов: {{count}}',
};

export function DevBlogPostPicker({ open, selected, onClose, onSubmit }: DevBlogPostPickerProps): React.ReactElement | null {
  const [query, setQuery] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [items, setItems] = React.useState<NodeItem[]>([]);
  const [selectedIds, setSelectedIds] = React.useState<Set<string>>(new Set(selected));

  React.useEffect(() => {
    if (!open) {
      return;
    }
    setSelectedIds(new Set(selected));
  }, [open, selected]);

  React.useEffect(() => {
    if (!open) {
      return;
    }
    const controller = new AbortController();
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchNodesList({
          tag: DEV_BLOG_TAG,
          q: query.trim(),
          status: 'published',
          limit: 25,
          signal: controller.signal,
        });
        setItems(response.items);
      } catch (err) {
        if ((err as Error)?.name === 'AbortError') {
          return;
        }
        setError(extractErrorMessage(err, translate(LOAD_ERROR_TEXT)));
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    };
    void run();
    return () => controller.abort();
  }, [open, query]);

  const handleToggle = React.useCallback((id: string, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  }, []);

  const handleSubmit = React.useCallback(() => {
    onSubmit(Array.from(selectedIds));
    onClose();
  }, [onClose, onSubmit, selectedIds]);

  const handleClose = React.useCallback(() => {
    setSelectedIds(new Set(selected));
    onClose();
  }, [onClose, selected]);

  if (!open) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      title={translate({ en: 'Select Dev Blog posts', ru: 'Выбор постов дев-блога' })}
      size="lg"
    >
      <div className="space-y-4">
        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={translate(SEARCH_PLACEHOLDER)}
        />
        {error ? (
          <div className="rounded border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-400/60 dark:bg-rose-950/20 dark:text-rose-200">
            {error}
          </div>
        ) : null}
        <div className="max-h-80 overflow-y-auto rounded-md border border-gray-200 dark:border-dark-500">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner />
            </div>
          ) : items.length === 0 ? (
            <div className="py-12 text-center text-sm text-gray-500 dark:text-dark-300">
              {translate(EMPTY_RESULT_TEXT)}
            </div>
          ) : (
            items.map((item) => {
              const key = item.id;
              const checked = selectedIds.has(key);
              const title = item.title?.trim() || translate(UNTITLED_POST_TEXT);
              const slug = item.slug?.trim() || key;
              return (
                <div
                  key={key}
                  className={`flex items-center justify-between gap-4 border-b border-gray-200 px-4 py-3 last:border-b-0 dark:border-dark-600 ${checked ? 'bg-primary-50/70 dark:bg-primary-900/20' : ''}`}
                >
                  <div className="min-w-0">
                    <div className="truncate font-medium text-gray-900 dark:text-dark-100">{title}</div>
                    <div className="truncate text-xs text-gray-500 dark:text-dark-300">{slug}</div>
                  </div>
                  <Checkbox
                    checked={checked}
                    onChange={(event) => handleToggle(key, event.currentTarget.checked)}
                    aria-label={title}
                  />
                </div>
              );
            })
          )}
        </div>
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-500 dark:text-dark-300">
            {translateWithVars(SELECTED_COUNT_TEXT, { count: String(selectedIds.size) })}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={handleClose}>
              {translate({ en: 'Cancel', ru: 'Отмена' })}
            </Button>
            <Button onClick={handleSubmit} disabled={selectedIds.size === 0}>
              {translate({ en: 'Apply', ru: 'Применить' })}
            </Button>
          </div>
        </div>
      </div>
    </Dialog>
  );
}
