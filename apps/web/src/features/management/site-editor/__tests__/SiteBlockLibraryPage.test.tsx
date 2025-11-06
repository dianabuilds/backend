import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ToastProvider } from '@ui';

import SiteBlockLibraryPage from '../components/SiteBlockLibraryPage';
import type {
  SiteBlock,
  SiteBlockDetailResponse,
  SiteBlockHistoryResponse,
  SiteBlockListResponse,
} from '@shared/types/management';

const apiMocks = vi.hoisted(() => ({
  fetchSiteBlocks: vi.fn(),
  fetchSiteBlock: vi.fn(),
  createSiteBlock: vi.fn(),
  saveSiteBlock: vi.fn(),
  publishSiteBlock: vi.fn(),
  archiveSiteBlock: vi.fn(),
  fetchSiteBlockHistory: vi.fn(),
  restoreSiteBlockVersion: vi.fn(),
}));

vi.mock('@shared/api/management', () => ({
  managementSiteEditorApi: apiMocks,
}));

const {
  fetchSiteBlocks: mockedFetchSiteBlocks,
  fetchSiteBlock: mockedFetchSiteBlock,
  createSiteBlock: mockedCreateSiteBlock,
  saveSiteBlock: mockedSaveSiteBlock,
  publishSiteBlock: mockedPublishSiteBlock,
  fetchSiteBlockHistory: mockedFetchSiteBlockHistory,
} = apiMocks;

function renderPage(): ReturnType<typeof render> {
  return render(
    <ToastProvider>
      <SiteBlockLibraryPage />
    </ToastProvider>,
  );
}

const SHARED_BLOCK: SiteBlock = {
  id: 'block-shared',
  key: 'header-template',
  title: 'Хедер',
  section: 'header',
  status: 'draft',
  review_status: 'none',
  requires_publisher: true,
  scope: 'shared',
  locale: 'ru',
  default_locale: 'ru',
  available_locales: ['ru', 'en'],
  published_version: null,
  draft_version: 2,
  version: 2,
  usage_count: 3,
  comment: null,
  data: {},
  meta: {},
  updated_at: '2025-11-01T10:00:00Z',
  updated_by: 'editor@caves.dev',
  has_pending_publish: null,
  extras: {},
  is_template: false,
  origin_block_id: null,
};

const PAGE_BLOCK: SiteBlock = {
  id: 'block-page',
  key: 'promo-banner-123',
  title: 'Промо баннер',
  section: 'promo',
  status: 'draft',
  review_status: 'none',
  requires_publisher: false,
  scope: 'page',
  locale: 'ru',
  default_locale: 'ru',
  available_locales: ['ru'],
  published_version: null,
  draft_version: 1,
  version: 1,
  usage_count: 0,
  comment: null,
  data: {},
  meta: {},
  updated_at: '2025-11-02T12:00:00Z',
  updated_by: 'designer@caves.dev',
  has_pending_publish: null,
  extras: {},
  is_template: false,
  origin_block_id: null,
};

const BLOCKS_RESPONSE: SiteBlockListResponse = {
  items: [SHARED_BLOCK, PAGE_BLOCK],
  page: 1,
  page_size: 50,
  total: 2,
};

const SHARED_DETAIL_RESPONSE: SiteBlockDetailResponse = {
  block: SHARED_BLOCK,
  usage: [],
  warnings: [],
};

const EMPTY_HISTORY: SiteBlockHistoryResponse = {
  items: [],
  total: 0,
  limit: 20,
  offset: 0,
};

describe('SiteBlockLibraryPage', () => {
  beforeEach(() => {
    mockedFetchSiteBlocks.mockResolvedValue(BLOCKS_RESPONSE);
    mockedFetchSiteBlock.mockResolvedValue(SHARED_DETAIL_RESPONSE);
    mockedFetchSiteBlockHistory.mockResolvedValue(EMPTY_HISTORY);
    mockedSaveSiteBlock.mockResolvedValue(SHARED_BLOCK);
    mockedCreateSiteBlock.mockResolvedValue({
      ...SHARED_BLOCK,
      id: 'block-new',
      key: 'new-shared',
      title: 'Новый блок',
    });
    mockedPublishSiteBlock.mockResolvedValue({ block: SHARED_BLOCK, usage: [], warnings: [] });
  });

  it('загружает список блоков и показывает детали первого shared-блока', async () => {
    renderPage();

    await waitFor(() => expect(mockedFetchSiteBlocks).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mockedFetchSiteBlock).toHaveBeenCalledTimes(1));
    await screen.findByText('Хедер');

    const detailPanel = screen.getByTestId('site-block-library-detail');
    expect(within(detailPanel).getByDisplayValue('Хедер')).toBeInTheDocument();
    expect(within(detailPanel).getByText('Общий блок')).toBeInTheDocument();
  });

  it('сохраняет изменения без поля meta.library', async () => {
    renderPage();
    await screen.findByDisplayValue('Хедер');

    const titleInput = screen.getByLabelText('Название');
    await userEvent.clear(titleInput);
    await userEvent.type(titleInput, 'Хедер (обновлён)');

    const saveButton = screen.getByRole('button', { name: 'Сохранить' });
    await userEvent.click(saveButton);

    await waitFor(() => expect(mockedSaveSiteBlock).toHaveBeenCalledTimes(1));
    const payload = mockedSaveSiteBlock.mock.calls[0][1];
    expect(payload.meta).toBeUndefined();
    expect(payload.title).toBe('Хедер (обновлён)');
    expect(payload.version).toBe(SHARED_BLOCK.version);
    expect(payload.is_template).toBe(false);
    expect(payload.origin_block_id).toBeNull();
  });

  it('создаёт новый блок с областью shared по умолчанию', async () => {
    renderPage();
    await screen.findByText('Сводка');

    await userEvent.click(screen.getByRole('button', { name: 'Создать блок' }));

    const dialog = screen.getByRole('dialog', { name: 'Создание блока' });
    await userEvent.type(within(dialog).getByLabelText('Ключ'), 'new-shared');
    await userEvent.type(within(dialog).getByLabelText('Название'), 'Новый блок');
    await userEvent.type(within(dialog).getByLabelText('Секция'), 'promo');

    await userEvent.click(within(dialog).getByRole('button', { name: 'Создать' }));

    await waitFor(() => expect(mockedCreateSiteBlock).toHaveBeenCalledTimes(1));
    const payload = mockedCreateSiteBlock.mock.calls[0][0];
    expect(payload.scope).toBe('shared');
    expect(payload.meta).toBeUndefined();
    expect(payload.is_template).toBe(false);
    expect(payload.origin_block_id).toBeNull();
  });

  it('делает публикацию недоступной для шаблона', async () => {
    const templateBlock: SiteBlock = {
      ...SHARED_BLOCK,
      id: 'block-template',
      is_template: true,
    };
    mockedFetchSiteBlocks.mockResolvedValueOnce({
      items: [templateBlock],
      page: 1,
      page_size: 50,
      total: 1,
    });
    mockedFetchSiteBlock.mockResolvedValueOnce({
      block: templateBlock,
      usage: [],
      warnings: [],
    });

    renderPage();

    await screen.findByText('Хедер');
    const publishButton = await screen.findByRole('button', { name: 'Опубликовать' });
    expect(publishButton).toBeDisabled();
  });
});
