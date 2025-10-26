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
} from '@shared/types/management';

vi.mock('@shared/api/management', () => ({
  managementSiteEditorApi: {
    fetchSitePages: vi.fn(),
    fetchSitePageHistory: vi.fn(),
    fetchSiteAudit: vi.fn(),
    restoreSitePageVersion: vi.fn(),
  },
}));

vi.mock('@shared/ui/toastBus', () => ({
  pushGlobalToast: vi.fn(),
}));

const mockedFetchPages = vi.mocked(managementSiteEditorApi.fetchSitePages);
const mockedFetchHistory = vi.mocked(managementSiteEditorApi.fetchSitePageHistory);
const mockedFetchAudit = vi.mocked(managementSiteEditorApi.fetchSiteAudit);
const mockedRestore = vi.mocked(managementSiteEditorApi.restoreSitePageVersion);

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
    },
  ],
  page: 1,
  page_size: 20,
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
  limit: 20,
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
    mockedFetchHistory.mockReset();
    mockedFetchAudit.mockReset();
    mockedRestore.mockReset();

    mockedFetchPages.mockResolvedValue(SAMPLE_RESPONSE);
    mockedFetchHistory.mockResolvedValue(HISTORY_RESPONSE);
    mockedFetchAudit.mockResolvedValue(AUDIT_RESPONSE);
    mockedRestore.mockResolvedValue(RESTORE_RESPONSE);
  });

  it('renders list and updates selection', async () => {
    const user = userEvent.setup();
    renderCatalog();

    await screen.findAllByText('Главная страница');
    expect(mockedFetchPages).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(mockedFetchHistory).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mockedFetchAudit).toHaveBeenCalledTimes(1));

    const detailCard = screen.getByTestId('site-page-detail');
    expect(detailCard).toBeInTheDocument();
    expect(detailCard).toHaveTextContent('/');
    expect(detailCard).toHaveTextContent('marketing');
    const rows = screen.getAllByRole('row');
    const firstDataRow = rows.find((row) => within(row).queryByText('Главная страница')) ?? rows[1];
    const actionButton = within(firstDataRow).getByRole('link', { name: 'Открыть' });
    expect(actionButton).toHaveAttribute('href', '/management/site-editor/pages/page-home');

    await user.click(screen.getByText('/help'));
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



