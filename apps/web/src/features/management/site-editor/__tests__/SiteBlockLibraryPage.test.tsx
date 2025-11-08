import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import SiteBlockLibraryPage from '../components/SiteBlockLibraryPage';
import type { SiteBlock, SiteBlockListResponse } from '@shared/types/management';

const apiMocks = vi.hoisted(() => ({
  fetchSiteBlocks: vi.fn(),
}));

vi.mock('@shared/api/management', () => ({
  managementSiteEditorApi: apiMocks,
}));

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

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
  ...SHARED_BLOCK,
  id: 'block-page',
  key: 'promo-banner-123',
  title: 'Промо баннер',
  section: 'promo',
  requires_publisher: false,
  scope: 'page',
  updated_at: '2025-11-02T12:00:00Z',
};

const BLOCKS_RESPONSE: SiteBlockListResponse = {
  items: [SHARED_BLOCK, PAGE_BLOCK],
  page: 1,
  page_size: 50,
  total: 2,
};

const { fetchSiteBlocks: mockedFetchSiteBlocks } = apiMocks;

describe('SiteBlockLibraryPage', () => {
  beforeEach(() => {
    mockedFetchSiteBlocks.mockReset().mockResolvedValue(BLOCKS_RESPONSE);
    mockNavigate.mockReset();
  });

  it('загружает и показывает список блоков', async () => {
    render(<SiteBlockLibraryPage />);

    await waitFor(() => expect(mockedFetchSiteBlocks).toHaveBeenCalledTimes(1));
    expect(await screen.findByText('Хедер')).toBeInTheDocument();
    expect(screen.getByText('Промо баннер')).toBeInTheDocument();
  });

  it('не показывает шаблонные блоки', async () => {
    mockedFetchSiteBlocks.mockResolvedValueOnce({
      items: [
        {
          ...SHARED_BLOCK,
          id: 'template-block',
          title: 'Шаблон',
          is_template: true,
        },
      ],
      page: 1,
      page_size: 50,
      total: 1,
    });

    render(<SiteBlockLibraryPage />);

    await waitFor(() => expect(mockedFetchSiteBlocks).toHaveBeenCalledTimes(1));
    expect(screen.queryByText('Шаблон')).not.toBeInTheDocument();
  });

  it('переходит к деталям блока по клику', async () => {
    render(<SiteBlockLibraryPage />);

    const button = await screen.findByRole('button', { name: /Хедер/ });
    await userEvent.click(button);

    expect(mockNavigate).toHaveBeenCalledWith('/management/site-editor/blocks/block-shared');
  });

  it('показывает сообщение об ошибке при сбое API', async () => {
    mockedFetchSiteBlocks.mockRejectedValueOnce(new Error('network error'));

    render(<SiteBlockLibraryPage />);

    await waitFor(() => expect(screen.getByText('Не удалось загрузить блоки')).toBeInTheDocument());
  });
});
