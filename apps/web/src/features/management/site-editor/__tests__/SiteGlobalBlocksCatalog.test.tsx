import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import SiteGlobalBlocksCatalog from '../components/SiteGlobalBlocksCatalog';
import { managementSiteEditorApi } from '@shared/api/management';
import type {
  SiteGlobalBlockDetailResponse,
  SiteGlobalBlockHistoryResponse,
  SiteGlobalBlockListResponse,
  SiteGlobalBlockMetricsResponse,
  SiteGlobalBlockPublishResponse,
} from '@shared/types/management';

vi.mock('@shared/api/management', () => ({
  managementSiteEditorApi: {
    fetchSiteGlobalBlocks: vi.fn(),
    fetchSiteGlobalBlock: vi.fn(),
    fetchSiteGlobalBlockHistory: vi.fn(),
    fetchSiteGlobalBlockMetrics: vi.fn(),
    saveSiteGlobalBlock: vi.fn(),
    publishSiteGlobalBlock: vi.fn(),
  },
}));

const mockedFetchGlobalBlocks = vi.mocked(managementSiteEditorApi.fetchSiteGlobalBlocks);
const mockedFetchGlobalBlock = vi.mocked(managementSiteEditorApi.fetchSiteGlobalBlock);
const mockedFetchGlobalBlockHistory = vi.mocked(managementSiteEditorApi.fetchSiteGlobalBlockHistory);
const mockedFetchGlobalBlockMetrics = vi.mocked(managementSiteEditorApi.fetchSiteGlobalBlockMetrics);
const mockedSaveGlobalBlock = vi.mocked(managementSiteEditorApi.saveSiteGlobalBlock);
const mockedPublishGlobalBlock = vi.mocked(managementSiteEditorApi.publishSiteGlobalBlock);

const LIST_RESPONSE: SiteGlobalBlockListResponse = {
  items: [
    {
      id: 'block-hero',
      key: 'global.hero',
      title: 'Hero banner',
      section: 'header',
      locale: 'ru',
      status: 'published',
      review_status: 'approved',
      requires_publisher: true,
      published_version: 5,
      draft_version: 7,
      usage_count: 3,
      comment: 'Основной баннер',
      data: {},
      meta: {},
      updated_at: '2025-10-25T09:00:00Z',
      updated_by: 'editor@caves.dev',
      has_pending_publish: false,
    },
    {
      id: 'block-footer',
      key: 'global.footer',
      title: 'Footer links',
      section: 'footer',
      locale: 'en',
      status: 'draft',
      review_status: 'pending',
      requires_publisher: false,
      published_version: 2,
      draft_version: 4,
      usage_count: 1,
      comment: null,
      data: {},
      meta: {},
      updated_at: '2025-10-24T12:15:00Z',
      updated_by: 'author@caves.dev',
      has_pending_publish: true,
    },
  ],
  page: 1,
  page_size: 10,
  total: 2,
};

const DETAIL_RESPONSE: SiteGlobalBlockDetailResponse = {
  block: {
    ...LIST_RESPONSE.items[0],
    usage_count: 3,
    comment: 'Основной баннер',
  },
  usage: [
    {
      block_id: 'block-hero',
      page_id: 'page-home',
      slug: '/',
      title: 'Главная страница',
      status: 'published',
      section: 'hero',
      locale: 'ru',
      has_draft: true,
      last_published_at: '2025-10-25T09:30:00Z',
    },
  ],
  warnings: [
    {
      code: 'missing-locale',
      page_id: 'page-help',
      message: 'Нет данных для локали en',
    },
  ],
};

const HISTORY_RESPONSE: SiteGlobalBlockHistoryResponse = {
  items: [
    {
      id: 'version-5',
      block_id: 'block-hero',
      version: 5,
      data: { blocks: [] },
      meta: { title: 'Hero banner' },
      comment: 'Выпущен новый баннер',
      diff: [
        { type: 'data', field: 'title', change: 'updated', before: 'Hero', after: 'Hero banner' },
      ],
      published_at: '2025-10-25T09:10:00Z',
      published_by: 'publisher@caves.dev',
    },
  ],
  total: 1,
  limit: 10,
  offset: 0,
};

const METRICS_RESPONSE: SiteGlobalBlockMetricsResponse = {
  block_id: 'block-hero',
  period: '7d',
  range: {
    start: '2025-10-18T00:00:00Z',
    end: '2025-10-25T00:00:00Z',
  },
  status: 'ok',
  source_lag_ms: 0,
  metrics: {
    impressions: { value: 1200, delta: 0.12 },
    clicks: { value: 96, delta: 0.05 },
  },
  alerts: [
    {
      code: 'ctr-drop',
      severity: 'warning',
      message: 'CTR упал ниже среднего за неделю',
    },
  ],
  top_pages: [
    {
      page_id: 'page-home',
      slug: '/',
      title: 'Главная страница',
      impressions: 800,
      clicks: 64,
      ctr: 0.08,
    },
  ],
};

const REVIEW_PENDING_BLOCK = {
  ...LIST_RESPONSE.items[0],
  review_status: 'pending' as const,
};

const PUBLISH_RESPONSE: SiteGlobalBlockPublishResponse = {
  id: 'block-hero',
  block: {
    ...LIST_RESPONSE.items[0],
    status: 'published',
    draft_version: 7,
    published_version: 7,
    has_pending_publish: false,
  },
  usage: DETAIL_RESPONSE.usage,
  affected_pages: [],
  jobs: [],
  audit_id: 'audit-1',
  published_version: 7,
};

function renderCatalog() {
  return render(
    <MemoryRouter>
      <SiteGlobalBlocksCatalog />
    </MemoryRouter>,
  );
}

describe('SiteGlobalBlocksCatalog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedFetchGlobalBlocks.mockResolvedValue(LIST_RESPONSE);
    mockedFetchGlobalBlock.mockResolvedValue(DETAIL_RESPONSE);
    mockedFetchGlobalBlockHistory.mockResolvedValue(HISTORY_RESPONSE);
    mockedFetchGlobalBlockMetrics.mockResolvedValue(METRICS_RESPONSE);
    mockedSaveGlobalBlock.mockResolvedValue(REVIEW_PENDING_BLOCK);
    mockedPublishGlobalBlock.mockResolvedValue(PUBLISH_RESPONSE);
  });

  it('отображает список блоков и детали выбранного элемента', async () => {
    const user = userEvent.setup();
    renderCatalog();

    await screen.findByText('Создать глобальный блок');

    const items = await screen.findAllByTestId('site-global-block-item');
    expect(items).toHaveLength(2);
    expect(mockedFetchGlobalBlocks).toHaveBeenCalledTimes(1);

    await waitFor(() => expect(mockedFetchGlobalBlock).toHaveBeenCalledWith('block-hero', expect.any(Object)));
    await waitFor(() => expect(mockedFetchGlobalBlockHistory).toHaveBeenCalledWith('block-hero', { limit: 10 }, expect.any(Object)));
    await waitFor(() => expect(mockedFetchGlobalBlockMetrics).toHaveBeenCalledWith('block-hero', { period: '7d' }, expect.any(Object)));

    const detailHeading = await screen.findByRole('heading', { name: 'Карточка блока' });
    const detailContainer = detailHeading.parentElement?.parentElement?.parentElement;
    expect(detailContainer).toBeTruthy();
    if (!detailContainer) {
      throw new Error('Не найдена секция деталей блока');
    }

    expect(within(detailContainer).getAllByText('Hero banner')[0]).toBeInTheDocument();
    expect(within(detailContainer).getByText('global.hero')).toBeInTheDocument();
    expect(within(detailContainer).getByText(/Комментарий:/)).toBeInTheDocument();
    expect(
      within(detailContainer).getByText((text) => text.includes('Основной баннер')),
    ).toBeInTheDocument();
    expect(within(detailContainer).getByText('Нет данных для локали en')).toBeInTheDocument();
    expect(within(detailContainer).getAllByText('Главная страница')[0]).toBeInTheDocument();

    await user.click(items[1]);
    await waitFor(() => expect(mockedFetchGlobalBlock).toHaveBeenCalledWith('block-footer', expect.any(Object)));
  });

  it('применяет фильтр по статусу и перезапрашивает данные', async () => {
    const user = userEvent.setup();
    renderCatalog();

    await screen.findAllByTestId('site-global-block-item');
    expect(mockedFetchGlobalBlocks).toHaveBeenCalledTimes(1);

    const statusSelect = screen.getByLabelText('Фильтр по статусу');
    await user.selectOptions(statusSelect, 'draft');

    await waitFor(() => expect(mockedFetchGlobalBlocks).toHaveBeenCalledTimes(2));
    const lastCallIndex = mockedFetchGlobalBlocks.mock.calls.length - 1;
    const lastCallArgs = lastCallIndex >= 0 ? mockedFetchGlobalBlocks.mock.calls[lastCallIndex] : undefined;
    expect(lastCallArgs?.[0]).toMatchObject({ status: 'draft' });
  });

  it('перезагружает детали и метрики по кнопкам', async () => {
    const user = userEvent.setup();
    renderCatalog();

    await screen.findAllByTestId('site-global-block-item');
    await waitFor(() => expect(mockedFetchGlobalBlock).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mockedFetchGlobalBlockMetrics).toHaveBeenCalledTimes(1));

    const refreshDetails = await screen.findByRole('button', { name: 'Обновить детали' });
    await user.click(refreshDetails);
    await waitFor(() => expect(mockedFetchGlobalBlock).toHaveBeenCalledTimes(2));

    const refreshMetrics = screen.getByRole('button', { name: 'Обновить метрики' });
    await user.click(refreshMetrics);
    await waitFor(() => expect(mockedFetchGlobalBlockMetrics).toHaveBeenCalledTimes(2));
  });

  it('позволяет использовать быстрые действия', async () => {
    const user = userEvent.setup();
    renderCatalog();

    const items = await screen.findAllByTestId('site-global-block-item');
    const firstItem = items[0];

    const reviewButton = within(firstItem).getByRole('button', { name: 'Отправить на ревью' });
    await user.click(reviewButton);

    await waitFor(() =>
      expect(mockedSaveGlobalBlock).toHaveBeenCalledWith('block-hero', { review_status: 'pending' }),
    );
    await waitFor(() => expect(reviewButton).toBeDisabled());

    const publishButton = within(firstItem).getByRole('button', { name: 'Опубликовать' });
    await user.click(publishButton);

    await waitFor(() =>
      expect(mockedPublishGlobalBlock).toHaveBeenCalledWith('block-hero', {
        version: LIST_RESPONSE.items[0].draft_version,
      }),
    );
    await waitFor(() => expect(publishButton).toBeDisabled());
  });
});
