import type { SiteBlock, SiteBlockStatus } from '@shared/types/management';

export type StatusMeta = {
  label: string;
  color: 'success' | 'warning' | 'neutral';
};

export const STATUS_META: Record<SiteBlockStatus, StatusMeta> = {
  published: { label: 'Опубликован', color: 'success' },
  draft: { label: 'Черновик', color: 'warning' },
  archived: { label: 'Архив', color: 'neutral' },
};

export const STATUS_ORDER: Record<SiteBlockStatus, number> = {
  published: 0,
  draft: 1,
  archived: 2,
};

export const SCOPE_LABELS: Record<string, string> = {
  shared: 'Общий блок',
  page: 'Страничный блок',
  unknown: 'Без области',
};

export const BLOCK_SCOPE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'shared', label: SCOPE_LABELS.shared },
  { value: 'page', label: SCOPE_LABELS.page },
];

export const REVIEW_STATUS_OPTIONS: Array<{ value: SiteBlock['review_status']; label: string }> = [
  { value: 'none', label: 'Ревью не требуется' },
  { value: 'pending', label: 'На ревью' },
  { value: 'approved', label: 'Одобрено' },
  { value: 'rejected', label: 'Отклонено' },
];

export const REVIEW_STATUS_META: Record<
  SiteBlock['review_status'],
  { label: string; color: 'neutral' | 'warning' | 'success' | 'error' }
> = {
  none: { label: 'Без ревью', color: 'neutral' },
  pending: { label: 'На ревью', color: 'warning' },
  approved: { label: 'Одобрено', color: 'success' },
  rejected: { label: 'Отклонено', color: 'error' },
};

export const HISTORY_PAGE_SIZE = 20;
export const BLOCKS_PAGE_SIZE = 100;
