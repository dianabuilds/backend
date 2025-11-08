import React from 'react';
import { Link } from 'react-router-dom';
import { Badge, Button, Card } from '@ui';
import { formatDateTime } from '@shared/utils/format';
import type { HomeDraftSnapshot } from '../../home/types';

type SitePageHeaderProps = {
  pageTitle: string;
  pageSlug: string;
  activeLocale: string;
  pageStatusBadge: { label: string; color: 'neutral' | 'info' | 'warning' | 'success' | 'error' | 'primary' } | null;
  pageTypeLabel?: string | null;
  snapshot: HomeDraftSnapshot;
  publishedVersion?: number | null;
  lastSavedAt: string | null;
  dirty: boolean;
  saving: boolean;
  publishing: boolean;
  loading: boolean;
  canPublish: boolean;
  onRefresh: () => void;
  onSaveDraft: () => void;
  onOpenPublish: () => void;
};

type StatProps = {
  label: string;
  value: string;
  hint?: string | null;
};

function StatCard({ label, value, hint }: StatProps): React.ReactElement {
  return (
    <div className="rounded-2xl border border-white/60 bg-white/80 px-4 py-3 shadow-sm backdrop-blur dark:border-dark-600/60 dark:bg-dark-800/70">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">{label}</div>
      <div className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">{value}</div>
      {hint ? <div className="mt-0.5 text-[11px] text-gray-500 dark:text-dark-200/80">{hint}</div> : null}
    </div>
  );
}

function formatDisplayDate(value: string | null): string {
  if (!value) {
    return '—';
  }
  return formatDateTime(value, {
    fallback: '—',
    withSeconds: true,
  });
}

export function SitePageHeader({
  pageTitle,
  pageSlug,
  activeLocale,
  pageStatusBadge,
  pageTypeLabel,
  snapshot,
  publishedVersion,
  lastSavedAt,
  dirty,
  saving,
  publishing,
  loading,
  canPublish,
  onRefresh,
  onSaveDraft,
  onOpenPublish,
}: SitePageHeaderProps): React.ReactElement {
  const draftVersion = snapshot.version ? `v${snapshot.version}` : '—';
  const draftUpdatedHint = snapshot.updatedAt ? `Обновлён ${formatDisplayDate(snapshot.updatedAt)}` : null;
  const publishedLabel = publishedVersion != null ? `v${publishedVersion}` : '—';
  const publishedHint = snapshot.publishedAt ? `Публик. ${formatDisplayDate(snapshot.publishedAt)}` : null;
  const lastSavedLabel = lastSavedAt ? formatDisplayDate(lastSavedAt) : '—';

  return (
    <Card className="rounded-3xl border border-white/60 bg-white/80 p-5 shadow-sm backdrop-blur dark:border-dark-600/60 dark:bg-dark-800/70 sm:p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <nav aria-label="Хлебные крошки" className="flex flex-wrap items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
            <Link to="/management/site-editor" className="transition-colors hover:text-primary-600 dark:hover:text-primary-300">
              Назад к списку страниц
            </Link>
            <span className="opacity-40">/</span>
            <span className="text-gray-600 dark:text-dark-100">Редактор страницы</span>
          </nav>

          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2 lg:gap-3">
              <h1 className="text-xl font-semibold tracking-tight text-gray-900 dark:text-white sm:text-2xl">
                {pageTitle || 'Страница'}
              </h1>
              {pageStatusBadge ? <Badge color={pageStatusBadge.color}>{pageStatusBadge.label}</Badge> : null}
              {pageTypeLabel ? <Badge variant="outline">{pageTypeLabel}</Badge> : null}
              {dirty ? <Badge color="warning">Есть несохранённые изменения</Badge> : <Badge color="success">Черновик актуален</Badge>}
              {saving ? <Badge color="info">Сохранение…</Badge> : null}
              {publishing ? <Badge color="info">Публикация…</Badge> : null}
            </div>
            <p className="text-sm text-gray-500 dark:text-dark-200">
              Конфиг страницы сохраняется автоматически при простое. Используйте действия справа, чтобы обновить данные или опубликовать изменения.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-end gap-2 lg:gap-3">
          <Button
            variant="outlined"
            color="neutral"
            onClick={onRefresh}
            disabled={loading || saving || publishing}
          >
            Обновить данные
          </Button>
          <Button onClick={onSaveDraft} disabled={!dirty || saving || publishing}>
            {saving ? 'Сохранение…' : dirty ? 'Сохранить черновик' : 'Сохранено'}
          </Button>
          {canPublish ? (
            <Button onClick={onOpenPublish} disabled={publishing || loading}>
              {publishing ? 'Публикация…' : 'Опубликовать'}
            </Button>
          ) : null}
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label={`Slug (${activeLocale.toUpperCase()})`}
          value={pageSlug || '—'}
          hint="Используется в URL публичной страницы выбранной локали"
        />
        <StatCard
          label="Черновик"
          value={draftVersion}
          hint={draftUpdatedHint ?? 'Черновик ещё не сохранялся'}
        />
        <StatCard
          label="Публикация"
          value={publishedLabel}
          hint={publishedHint ?? 'Изменения ещё не публиковались'}
        />
        <StatCard
          label="Последнее сохранение"
          value={lastSavedLabel}
          hint={dirty ? 'Изменения ожидают сохранения' : 'Черновик синхронизирован'}
        />
      </div>
    </Card>
  );
}

export default SitePageHeader;
