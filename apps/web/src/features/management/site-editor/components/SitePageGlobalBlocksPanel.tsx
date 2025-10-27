import React from 'react';
import { Badge, Button, Card, Select, Spinner } from '@ui';
import { AlertTriangle } from '@icons';
import { managementSiteEditorApi } from '@shared/api/management';
import type {
  SiteGlobalBlock,
  SitePageReviewStatus,
  SitePageSummary,
} from '@shared/types/management';
import { extractErrorMessage } from '@shared/utils/errors';
import { globalBlockStatusAppearance, reviewAppearance } from '../utils/pageHelpers';

type GlobalBlockOption = Pick<
  SiteGlobalBlock,
  | 'id'
  | 'key'
  | 'title'
  | 'section'
  | 'status'
  | 'review_status'
  | 'requires_publisher'
  | 'has_pending_publish'
>;

export type SitePageGlobalBlockOption = GlobalBlockOption;

type SelectionMap = Record<string, { key: string }>;

type SitePageGlobalBlocksPanelProps = {
  locale: SitePageSummary['locale'] | null | undefined;
  assignments: SelectionMap;
  onChange: (section: string, block: GlobalBlockOption | null) => void;
  disabled?: boolean;
};

function getSectionLabel(section: string): string {
  const normalized = section.trim().toLowerCase();
  switch (normalized) {
    case 'header':
      return 'Хедер';
    case 'footer':
      return 'Футер';
    case 'promo':
      return 'Промо-зона';
    case 'sidebar':
      return 'Сайдбар';
    default:
      return normalized ? normalized : 'Без зоны';
  }
}

function normalizeSection(section: string | null | undefined): string {
  if (typeof section === 'string' && section.trim()) {
    return section.trim();
  }
  return 'other';
}

export function SitePageGlobalBlocksPanel({
  locale,
  assignments,
  onChange,
  disabled = false,
}: SitePageGlobalBlocksPanelProps): React.ReactElement {
  const [options, setOptions] = React.useState<GlobalBlockOption[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [refreshKey, setRefreshKey] = React.useState(0);

  React.useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    managementSiteEditorApi
      .fetchSiteGlobalBlocks(
        {
          pageSize: 100,
          status: 'published',
          locale: locale?.trim() || undefined,
        },
        { signal: controller.signal },
      )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        const items = Array.isArray(response.items) ? response.items : [];
        const normalized = items
          .filter((item): item is GlobalBlockOption => Boolean(item?.key))
          .map((item) => ({
            id: item.id,
            key: item.key,
            title: item.title,
            section: item.section,
            status: item.status,
            review_status: item.review_status,
            requires_publisher: item.requires_publisher,
            has_pending_publish: item.has_pending_publish,
          }));
        setOptions(normalized);
      })
      .catch((err) => {
        if ((err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setError(extractErrorMessage(err, 'Не удалось загрузить глобальные блоки.'));
        setOptions([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });
    return () => controller.abort();
  }, [locale, refreshKey]);

  const optionsByKey = React.useMemo(() => {
    const map = new Map<string, GlobalBlockOption>();
    options.forEach((item) => {
      map.set(item.key, item);
    });
    return map;
  }, [options]);

  const groupedSections = React.useMemo(() => {
    const map = new Map<string, GlobalBlockOption[]>();
    options.forEach((item) => {
      const section = normalizeSection(item.section);
      if (!map.has(section)) {
        map.set(section, []);
      }
      map.get(section)!.push(item);
    });
    map.forEach((list) => {
      list.sort((a, b) => (a.title || a.key).localeCompare(b.title || b.key, 'ru'));
    });
    return map;
  }, [options]);

  const sections = React.useMemo(() => {
    const keys = new Set<string>();
    groupedSections.forEach((_value, section) => keys.add(section));
    Object.keys(assignments).forEach((section) => keys.add(section));
    if (keys.size === 0 && options.length === 0) {
      return ['header', 'footer'];
    }
    return Array.from(keys).sort((a, b) => a.localeCompare(b));
  }, [assignments, groupedSections, options.length]);

  const handleAssign = React.useCallback(
    (section: string, key: string) => {
      if (!key) {
        onChange(section, null);
        return;
      }
      const block = optionsByKey.get(key);
      if (block) {
        onChange(section, block);
      } else {
        onChange(section, {
          id: key,
          key,
          title: key,
          section,
          status: 'draft',
          review_status: 'none' as SitePageReviewStatus,
          requires_publisher: false,
          has_pending_publish: false,
        });
      }
    },
    [onChange, optionsByKey],
  );

  return (
    <Card
      padding="sm"
      className="space-y-4 border border-gray-200/70 bg-white/95 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/80"
    >
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">
            Глобальные блоки страницы
          </h3>
          <Button
            type="button"
            size="xs"
            variant="ghost"
            onClick={() => setRefreshKey((prev) => prev + 1)}
            disabled={loading}
          >
          {loading ? 'Обновляем...' : 'Обновить'}
          </Button>
        </div>
        <p className="text-xs text-gray-500 dark:text-dark-300">
          Выберите опубликованные глобальные блоки для зон страницы. Ссылки сохраняются в черновике и учитываются при публикации.
        </p>
        {locale ? (
          <div className="text-[11px] uppercase tracking-wide text-gray-400 dark:text-dark-400">
            Локаль страницы: <span className="font-semibold text-gray-600 dark:text-dark-100">{locale}</span>
          </div>
        ) : null}
      </div>

      {error ? (
        <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/40 dark:bg-rose-950/40 dark:text-rose-200">
          <AlertTriangle className="mt-0.5 h-4 w-4" />
          <span>{error}</span>
        </div>
      ) : null}

      {sections.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50 p-4 text-sm text-gray-500 dark:border-dark-600 dark:bg-dark-900/60 dark:text-dark-200">
          Нет доступных глобальных блоков для выбранной локали.
        </div>
      ) : null}

      <div className="space-y-4">
        {sections.map((section) => {
          const sectionKey = normalizeSection(section);
          const sectionOptions = groupedSections.get(sectionKey) ?? [];
          const assignedKey = assignments[sectionKey]?.key ?? '';
          const selectedOption =
            (assignedKey && optionsByKey.get(assignedKey)) ??
            (assignedKey
              ? {
                  id: assignedKey,
                  key: assignedKey,
                  title: assignedKey,
                  section: sectionKey,
                  status: 'draft' as SiteGlobalBlock['status'],
                  review_status: 'pending' as SitePageReviewStatus,
                  requires_publisher: false,
                  has_pending_publish: false,
                }
              : null);
          const statusAppearance = selectedOption
            ? globalBlockStatusAppearance(selectedOption.status)
            : null;
          const reviewMeta = selectedOption
            ? reviewAppearance(selectedOption.review_status)
            : null;

          return (
            <div
              key={sectionKey}
              className="rounded-2xl border border-gray-100/70 bg-white/90 p-4 shadow-inner dark:border-dark-600/40 dark:bg-dark-900/60"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-dark-50">
                    {getSectionLabel(sectionKey)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-dark-300">
                    Зона: <span className="font-mono text-gray-700 dark:text-dark-100">{sectionKey}</span>
                  </div>
                </div>
                {loading ? <Spinner className="h-4 w-4 text-primary-500" /> : null}
              </div>

              <div className="mt-3 grid gap-2 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
                <Select
                  aria-label={`Выбор глобального блока для зоны ${sectionKey}`}
                  value={assignedKey}
                  onChange={(event) => handleAssign(sectionKey, event.target.value)}
                  disabled={disabled || loading}
                >
                  <option value="">Не выбран</option>
                  {sectionOptions.map((option) => (
                    <option key={option.key} value={option.key}>
                      {option.title || option.key}
                    </option>
                  ))}
                  {assignedKey && !sectionOptions.some((option) => option.key === assignedKey) ? (
                    <option value={assignedKey}>{assignedKey} (недоступен)</option>
                  ) : null}
                </Select>
                {assignedKey ? (
                  <Button
                    type="button"
                    size="xs"
                    variant="ghost"
                    onClick={() => handleAssign(sectionKey, '')}
                    disabled={disabled || loading}
                  >
                    Очистить
                  </Button>
                ) : null}
              </div>

              {selectedOption ? (
                <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                  <Badge color={statusAppearance?.color ?? 'neutral'} variant="soft">
                    {statusAppearance?.label ?? 'Статус неизвестен'}
                  </Badge>
                  {reviewMeta ? (
                    <Badge color={reviewMeta.color} variant="outline">
                      {reviewMeta.label}
                    </Badge>
                  ) : null}
                  {selectedOption.requires_publisher ? (
                    <Badge color="warning" variant="soft">
                      Требует publisher
                    </Badge>
                  ) : null}
                  {selectedOption.has_pending_publish ? (
                    <Badge color="primary" variant="soft">
                      Есть черновик
                    </Badge>
                  ) : null}
                </div>
              ) : (
                <div className="mt-3 text-xs text-gray-500 dark:text-dark-300">
                  Блок не выбран - в зоне останется локальный контент страницы.
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
