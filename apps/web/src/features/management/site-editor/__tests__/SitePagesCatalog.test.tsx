import React from 'react';
import { describe, expect, it, beforeEach, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import SitePagesCatalog from '../components/SitePagesCatalog';
import { managementSiteEditorApi } from '@shared/api/management';
import type {
  SiteAuditListResponse,
  SitePageDraft,
  SitePageHistoryResponse,
  SitePageListResponse,
  SitePageSummary,
} from '@shared/types/management';

vi.mock('@shared/api/management', () => ({
  managementSiteEditorApi: {
    fetchSitePages: vi.fn(),
    fetchSitePage: vi.fn(),
    fetchSitePageHistory: vi.fn(),
    fetchSiteAudit: vi.fn(),
    restoreSitePageVersion: vi.fn(),
    createSitePage: vi.fn(),
    deleteSitePage: vi.fn(),
  },
}));

vi.mock('@shared/ui/toastBus', () => ({
  pushGlobalToast: vi.fn(),
}));

const mockedFetchPages = vi.mocked(managementSiteEditorApi.fetchSitePages);
const mockedFetchPage = vi.mocked(managementSiteEditorApi.fetchSitePage);
const mockedFetchHistory = vi.mocked(managementSiteEditorApi.fetchSitePageHistory);
const mockedFetchAudit = vi.mocked(managementSiteEditorApi.fetchSiteAudit);
const mockedRestore = vi.mocked(managementSiteEditorApi.restoreSitePageVersion);

const mockedCreatePage = vi.mocked(managementSiteEditorApi.createSitePage);
const mockedDeletePage = vi.mocked(managementSiteEditorApi.deleteSitePage);

const SAMPLE_RESPONSE: SitePageListResponse = {
  items: [
    {
      id: 'page-home',
      slug: '/',
      title: 'Главная страница',
      type: 'landing',
      status: 'published',
      locale: 'ru',
      owner: 'marketing',
      updated_at: '2025-10-25T09:00:00Z',
      published_version: 12,
      draft_version: 14,
      has_pending_review: false,
      pinned: true,
    },
    {
      id: 'page-help',
      slug: '/help',
      title: 'Справка',
      type: 'article',
      status: 'draft',
      locale: 'ru',
      owner: 'support',
      updated_at: '2025-10-24T11:30:00Z',
      published_version: 5,
      draft_version: 7,
      has_pending_review: true,
      pinned: false,
    },
  ],
  page: 1,
  page_size: 10,
  total: 2,
};

const HISTORY_RESPONSE: SitePageHistoryResponse = {
  items: [
    {
      id: 'version-2',
      page_id: 'page-home',
      version: 2,
      data: {},
      meta: {},
      comment: 'Второй релиз',
      diff: [
        { type: 'block', blockId: 'hero-1', change: 'updated' },
        { type: 'block', blockId: 'promo-1', change: 'added' },
      ],
      published_at: '2025-10-25T10:00:00Z',
      published_by: 'editor@caves.dev',
    },
  ],
  total: 1,
  limit: 10,
  offset: 0,
};

const AUDIT_RESPONSE: SiteAuditListResponse = {
  items: [
    {
      id: 'audit-1',
      entity_type: 'page',
      entity_id: 'page-home',
      action: 'publish',
      snapshot: { version: 2, comment: 'Второй релиз' },
      actor: 'editor@caves.dev',
      created_at: '2025-10-25T10:00:05Z',
    },
  ],
  total: 1,
  limit: 10,
  offset: 0,
};

const RESTORE_RESPONSE: SitePageDraft = {
  page_id: 'page-home',
  version: 3,
  data: {},
  meta: {},
  review_status: 'none',
  comment: null,
};

const CREATED_PAGE_RESPONSE: SitePageSummary = {
  id: 'page-new',
  slug: '/page-new',
  title: 'Новая страница',
  type: 'landing',
  status: 'draft',
  locale: 'ru',
  owner: 'marketing',
  updated_at: '2025-10-26T10:00:00Z',
  published_version: null,
  draft_version: 1,
  has_pending_review: false,
  pinned: false,
};

const PAGE_DETAILS: Record<string, SitePageSummary> = {
  'page-home': {
    id: 'page-home',
    slug: '/',
    title: 'Главная страница',
    type: 'landing',
    status: 'published',
    locale: 'ru',
    owner: 'marketing',
    updated_at: '2025-10-25T09:00:00Z',
    published_version: 12,
    draft_version: 14,
    has_pending_review: false,
    pinned: true,
    shared_bindings: [
      {
        key: 'header-nav',
        block_id: 'block-header',
        title: 'Header Nav',
        section: 'header',
        status: 'published',
        review_status: 'none',
        requires_publisher: true,
        published_version: 3,
        draft_version: 4,
        updated_at: '2025-10-25T08:55:00Z',
        updated_by: 'editor@caves.dev',
        locale: 'ru',
      },
    ],
  },
  'page-help': {
    id: 'page-help',
    slug: '/help',
    title: 'Справка',
    type: 'article',
    status: 'draft',
    locale: 'ru',
    owner: 'support',
    updated_at: '2025-10-24T11:30:00Z',
    published_version: 5,
    draft_version: 7,
    has_pending_review: true,
    pinned: false,
    shared_bindings: [],
  },
};

function renderCatalog() {
  return render(
    <MemoryRouter>
      <SitePagesCatalog />
    </MemoryRouter>,
  );
}

describe('SitePagesCatalog', () => {
  beforeEach(() => {
    mockedFetchPages.mockReset();
    mockedFetchPage.mockReset();
    mockedFetchHistory.mockReset();
    mockedFetchAudit.mockReset();
    mockedRestore.mockReset();

    mockedCreatePage.mockReset();
    mockedDeletePage.mockReset();

    mockedFetchPages.mockResolvedValue(SAMPLE_RESPONSE);
    mockedFetchPage.mockImplementation(async (pageId) => PAGE_DETAILS[pageId] ?? null);
    mockedFetchHistory.mockResolvedValue(HISTORY_RESPONSE);
    mockedFetchAudit.mockResolvedValue(AUDIT_RESPONSE);
    mockedRestore.mockResolvedValue(RESTORE_RESPONSE);
    mockedCreatePage.mockResolvedValue(CREATED_PAGE_RESPONSE);
    mockedDeletePage.mockResolvedValue(undefined);
  });

  it('renders list and updates selection', async () => {
    const user = userEvent.setup();
    renderCatalog();

    const pageItems = await screen.findAllByTestId('site-page-item');
    expect(mockedFetchPages).toHaveBeenCalledTimes(1);
    await waitFor(() => {
      expect(mockedFetchPage.mock.calls.some(([pageId]) => pageId === 'page-home')).toBe(true);
    });
    await waitFor(() => expect(mockedFetchHistory).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mockedFetchAudit).toHaveBeenCalledTimes(1));

    const detailCard = screen.getByTestId('site-page-detail');
    expect(detailCard).toBeInTheDocument();
    expect(detailCard).toHaveTextContent('/');
    expect(detailCard).toHaveTextContent('marketing');
    expect(detailCard).toHaveTextContent('Закреплена');
    expect(pageItems[0]).toHaveTextContent('Главная страница');
    expect(pageItems[0]).toHaveTextContent('Закреплена');
    const actionButton = within(pageItems[0]).getByRole('link', { name: 'Открыть' });
    expect(actionButton).toHaveAttribute('href', '/management/site-editor/pages/page-home');

    await user.click(screen.getByRole('button', { name: 'Выбрать страницу Справка' }));
    await waitFor(() => {
      expect(mockedFetchPage.mock.calls.some(([pageId]) => pageId === 'page-help')).toBe(true);
    });
    expect(detailCard).toHaveTextContent('support');
    expect(detailCard).toHaveTextContent('/help');
  });

  it('applies status filter and refetches data', async () => {
    const user = userEvent.setup();
    renderCatalog();

    await screen.findAllByText('Главная страница');
    expect(mockedFetchPages).toHaveBeenCalledTimes(1);

    const statusSelect = screen.getByLabelText('Фильтр по статусу');
    await user.selectOptions(statusSelect, 'draft');

    await waitFor(() => expect(mockedFetchPages).toHaveBeenCalledTimes(2));
    const lastCall = mockedFetchPages.mock.calls[mockedFetchPages.mock.calls.length - 1] ?? [];
    expect(lastCall[0]).toMatchObject({ status: 'draft' });
  });

  it('рендерит историю версий и выполняет восстановление', async () => {
    const user = userEvent.setup();
    renderCatalog();

    const versionHeader = await screen.findByText('Версия v2');
    const historyItem = versionHeader.closest('li');
    expect(historyItem).not.toBeNull();
    if (!historyItem) {
      throw new Error('history item not found');
    }
    expect(within(historyItem).getByText('Блок hero-1 обновлен')).toBeInTheDocument();
    expect(within(historyItem).getByText('Блок promo-1 добавлен')).toBeInTheDocument();

    const restoreButton = within(historyItem).getByRole('button', { name: 'Восстановить' });
    await user.click(restoreButton);

    await waitFor(() => expect(mockedRestore).toHaveBeenCalledWith('page-home', 2));
    await waitFor(() => expect(mockedFetchHistory).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(mockedFetchAudit).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(mockedFetchPages).toHaveBeenCalledTimes(2));
  });
});


