import type {
  SiteGlobalBlockStatus,
  SitePageReviewStatus,
  SitePageStatus,
  SitePageType,
} from '@shared/types/management';

export type StatusAppearance = {
  label: string;
  color: 'success' | 'warning' | 'neutral';
};

export function statusAppearance(status: SitePageStatus): StatusAppearance {
  switch (status) {
    case 'published':
      return { label: 'Опубликована', color: 'success' };
    case 'draft':
      return { label: 'Черновик', color: 'warning' };
    case 'archived':
    default:
      return { label: 'Архив', color: 'neutral' };
  }
}

export function typeLabel(type: SitePageType): string {
  switch (type) {
    case 'landing':
      return 'Лэндинг';
    case 'collection':
      return 'Коллекция';
    case 'article':
      return 'Статья';
    case 'system':
    default:
      return 'Системная';
  }
}

export type ReviewAppearance = {
  label: string;
  color: 'success' | 'warning' | 'error' | 'neutral';
};

export function reviewAppearance(
  status: SitePageReviewStatus | string | null | undefined,
): ReviewAppearance {
  switch (status) {
    case 'pending':
      return { label: 'На ревью', color: 'warning' };
    case 'approved':
      return { label: 'Одобрено', color: 'success' };
    case 'rejected':
      return { label: 'Отклонено', color: 'error' };
    case 'none':
      return { label: 'Ревью не требуется', color: 'neutral' };
    default:
      return { label: 'Ревью не задано', color: 'neutral' };
  }
}

export type GlobalBlockStatusAppearance = {
  label: string;
  color: 'success' | 'warning' | 'error' | 'neutral';
};

export function globalBlockStatusAppearance(
  status: SiteGlobalBlockStatus | string | null | undefined,
): GlobalBlockStatusAppearance {
  switch (status) {
    case 'published':
      return { label: 'Опубликован', color: 'success' };
    case 'draft':
      return { label: 'Черновик', color: 'warning' };
    case 'archived':
      return { label: 'Архив', color: 'neutral' };
    default:
      return { label: 'Неизвестно', color: 'neutral' };
  }
}
