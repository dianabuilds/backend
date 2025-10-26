import { describe, beforeEach, afterEach, it, expect, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';

import { managementSiteEditorApi } from '@shared/api/management';
import { useSitePageEditorState } from '../hooks/useSitePageEditorState';

vi.mock('@shared/api/management', () => ({
  managementSiteEditorApi: {
    fetchSitePage: vi.fn(),
    fetchSitePageDraft: vi.fn(),
    fetchSitePageHistory: vi.fn(),
    fetchSitePageMetrics: vi.fn(),
    fetchSiteAudit: vi.fn(),
    saveSitePageDraft: vi.fn(),
    restoreSitePageVersion: vi.fn(),
    publishSitePage: vi.fn(),
    diffSitePageDraft: vi.fn(),
    previewSitePage: vi.fn(),
    validateSitePageDraft: vi.fn(),
  },
}));

vi.mock('@shared/ui/toastBus', () => ({
  pushGlobalToast: vi.fn(),
}));

type MockedApi = {
  fetchSitePage: ReturnType<typeof vi.fn>;
  fetchSitePageDraft: ReturnType<typeof vi.fn>;
  fetchSitePageHistory: ReturnType<typeof vi.fn>;
  fetchSitePageMetrics: ReturnType<typeof vi.fn>;
  fetchSiteAudit: ReturnType<typeof vi.fn>;
  saveSitePageDraft: ReturnType<typeof vi.fn>;
  restoreSitePageVersion: ReturnType<typeof vi.fn>;
  publishSitePage: ReturnType<typeof vi.fn>;
  diffSitePageDraft: ReturnType<typeof vi.fn>;
  previewSitePage: ReturnType<typeof vi.fn>;
  validateSitePageDraft: ReturnType<typeof vi.fn>;
};

const mockedApi = managementSiteEditorApi as unknown as MockedApi;

describe('useSitePageEditorState', () => {
  const PAGE_SUMMARY = {
    id: 'page-home',
    slug: '/',
    title: 'Главная страница',
    type: 'landing' as const,
    status: 'draft' as const,
    locale: 'ru',
    owner: 'marketing',
    updated_at: '2025-10-25T09:00:00Z',
    published_version: 1,
    draft_version: 2,
    has_pending_review: false,
  };

  const DRAFT = {
    page_id: 'page-home',
    version: 2,
    data: {
      blocks: [
        { id: 'hero-1', type: 'hero', enabled: true, title: 'Hero' },
      ],
      meta: { title: 'Главная' },
    },
    meta: { title: 'Главная' },
    comment: null,
    review_status: 'none' as const,
    updated_at: '2025-10-25T09:40:00Z',
    updated_by: 'editor@caves.dev',
  };

  const HISTORY_RESPONSE = {
    items: [] as Array<unknown>,
    total: 0,
    limit: 10,
    offset: 0,
  };

  const AUDIT_RESPONSE = {
    items: [] as Array<unknown>,
    total: 0,
    limit: 10,
    offset: 0,
  };

  const DIFF_RESPONSE = {
    draft_version: DRAFT.version,
    published_version: PAGE_SUMMARY.published_version,
    diff: [] as Array<unknown>,
  };

  const PREVIEW_RESPONSE = {
    page: PAGE_SUMMARY,
    draft_version: DRAFT.version,
    published_version: PAGE_SUMMARY.published_version,
    requested_version: DRAFT.version,
    version_mismatch: false,
    layouts: {
      desktop: {
        layout: 'desktop',
        generated_at: '2025-10-25T09:40:00Z',
        data: DRAFT.data,
        meta: DRAFT.meta,
      },
      mobile: {
        layout: 'mobile',
        generated_at: '2025-10-25T09:40:00Z',
        data: DRAFT.data,
        meta: DRAFT.meta,
      },
    },
  };

  const METRICS_RESPONSE = {
    page_id: PAGE_SUMMARY.id,
    period: '7d',
    range: {
      start: '2025-10-18T00:00:00Z',
      end: '2025-10-25T00:00:00Z',
    },
    status: 'ok',
    source_lag_ms: 0,
    metrics: {
      views: { value: 1000, delta: 0.1 },
      ctr: { value: 0.05, delta: 0.02 },
    },
    alerts: [],
  };

  beforeEach(() => {
    mockedApi.fetchSitePage.mockResolvedValue(PAGE_SUMMARY);
    mockedApi.fetchSitePageDraft.mockResolvedValue(DRAFT);
    mockedApi.fetchSitePageHistory.mockResolvedValue(HISTORY_RESPONSE);
    mockedApi.fetchSitePageMetrics.mockResolvedValue(METRICS_RESPONSE);
    mockedApi.fetchSiteAudit.mockResolvedValue(AUDIT_RESPONSE);
    mockedApi.diffSitePageDraft.mockResolvedValue(DIFF_RESPONSE);
    mockedApi.previewSitePage.mockResolvedValue(PREVIEW_RESPONSE);
    mockedApi.validateSitePageDraft.mockResolvedValue({
      valid: true,
      data: DRAFT.data,
      meta: DRAFT.meta,
    });
    mockedApi.saveSitePageDraft.mockResolvedValue({
      ...DRAFT,
      version: DRAFT.version + 1,
      updated_at: '2025-10-25T09:45:00Z',
    });
    mockedApi.publishSitePage.mockResolvedValue({
      id: 'version-3',
      page_id: PAGE_SUMMARY.id,
      version: (PAGE_SUMMARY.published_version ?? 1) + 1,
      data: DRAFT.data,
      meta: DRAFT.meta,
      comment: null,
      diff: [],
      published_at: '2025-10-25T09:50:00Z',
      published_by: 'publisher@caves.dev',
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('сохраняет черновик вручную', async () => {
    const { result } = renderHook(() => useSitePageEditorState({ pageId: 'page-home', autosaveMs: 1000 }));

    await waitFor(() => expect(mockedApi.fetchSitePage).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(result.current.loading).toBe(false));
    await waitFor(() => expect(mockedApi.fetchSitePageMetrics).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mockedApi.previewSitePage).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mockedApi.diffSitePageDraft).toHaveBeenCalledTimes(1));

    await act(async () => {
      await result.current.saveDraft({ silent: false });
    });

    await waitFor(() => expect(mockedApi.saveSitePageDraft).toHaveBeenCalledTimes(1));
    expect(mockedApi.saveSitePageDraft.mock.calls[0][0]).toBe('page-home');
    await waitFor(() => expect(mockedApi.validateSitePageDraft).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mockedApi.previewSitePage).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(mockedApi.diffSitePageDraft).toHaveBeenCalledTimes(2));
  });

  it('автоматически сохраняет изменения после таймера', async () => {
    const autosaveMs = 30;

    const { result } = renderHook(() => useSitePageEditorState({ pageId: 'page-home', autosaveMs }));

    await waitFor(() => expect(mockedApi.fetchSitePage).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(result.current.loading).toBe(false));
    await waitFor(() => expect(mockedApi.fetchSitePageMetrics).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mockedApi.previewSitePage).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mockedApi.diffSitePageDraft).toHaveBeenCalledTimes(1));

    act(() => {
      const nextBlocks = result.current.data.blocks.map((block) => ({
        ...block,
        enabled: !block.enabled,
      }));
      result.current.setBlocks(nextBlocks);
    });

    expect(mockedApi.saveSitePageDraft).toHaveBeenCalledTimes(0);

    await waitFor(
      () => expect(mockedApi.saveSitePageDraft).toHaveBeenCalledTimes(1),
      { timeout: autosaveMs * 100 },
    );
    await waitFor(
      () => expect(mockedApi.validateSitePageDraft).toHaveBeenCalledTimes(1),
      { timeout: autosaveMs * 100 },
    );
    await waitFor(
      () => expect(mockedApi.previewSitePage).toHaveBeenCalledTimes(2),
      { timeout: autosaveMs * 100 },
    );
    await waitFor(
      () => expect(mockedApi.diffSitePageDraft).toHaveBeenCalledTimes(2),
      { timeout: autosaveMs * 100 },
    );
  });

  it('публикует страницу с комментарием', async () => {
    const { result } = renderHook(() => useSitePageEditorState({ pageId: 'page-home', autosaveMs: 1000 }));

    await waitFor(() => expect(mockedApi.fetchSitePage).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(result.current.loading).toBe(false));
    await waitFor(() => expect(mockedApi.fetchSitePageMetrics).toHaveBeenCalledTimes(1));

    await act(async () => {
      await result.current.publishDraft({ comment: 'hero updated' });
    });

    expect(mockedApi.publishSitePage).toHaveBeenCalledTimes(1);
    expect(mockedApi.publishSitePage.mock.calls[0][0]).toBe('page-home');
    expect(mockedApi.publishSitePage.mock.calls[0][1]).toEqual({ comment: 'hero updated' });
    await waitFor(() => expect(mockedApi.fetchSitePage).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(mockedApi.fetchSitePageMetrics).toHaveBeenCalledTimes(2));
  });
});
