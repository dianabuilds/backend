import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import DevBlogListPage from '../DevBlogListPage';
import { buildDevBlogListKey, DEV_BLOG_PAGE_SIZE } from '../DevBlogListPage.shared';
import { InitialDataProvider } from '@shared/ssr/InitialDataContext';
import { fetchDevBlogList } from '@shared/api/devBlog';
import type { DevBlogListResponse } from '@shared/types/devBlog';

vi.mock('@shared/api/devBlog', () => ({
  fetchDevBlogList: vi.fn(),
  fetchDevBlogPost: vi.fn(),
}));

const mockedFetchDevBlogList = vi.mocked(fetchDevBlogList);

const listResponse: DevBlogListResponse = {
  items: [
    {
      id: 1,
      slug: 'first-post',
      title: 'Первый пост',
      summary: 'Краткая выжимка обновлений недели.',
      coverUrl: null,
      publishAt: '2025-10-10T10:00:00Z',
      updatedAt: '2025-10-10T10:00:00Z',
      author: { id: '42', name: 'Команда' },
      tags: ['updates'],
    },
  ],
  total: 1,
  hasNext: false,
  availableTags: ['updates', 'releases'],
  dateRange: { start: '2025-10-01T00:00:00Z', end: '2025-10-10T10:00:00Z' },
  appliedTags: [],
};

function renderListPage(data: Record<string, unknown> | null = null, search = '') {
  return render(
    <HelmetProvider>
      <InitialDataProvider data={data ?? undefined}>
        <MemoryRouter initialEntries={[`/dev-blog${search}`]}>
          <Routes>
            <Route path="/dev-blog" element={<DevBlogListPage />} />
          </Routes>
        </MemoryRouter>
      </InitialDataProvider>
    </HelmetProvider>,
  );
}

beforeEach(() => {
  mockedFetchDevBlogList.mockReset();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('DevBlogListPage', () => {
  it('renders cached initial data without requesting API', () => {
    const key = buildDevBlogListKey(1, { tags: [], from: undefined, to: undefined });
    renderListPage({ [key]: listResponse });

    expect(screen.getByText('Первый пост')).toBeInTheDocument();
    expect(mockedFetchDevBlogList).not.toHaveBeenCalled();
  });

  it('shows error when request fails', async () => {
    mockedFetchDevBlogList.mockResolvedValue({ data: null, status: 500, error: 'boom' });

    renderListPage(null, '?page=2');

    await waitFor(() => {
      expect(screen.getByText('Не удалось загрузить посты: boom')).toBeInTheDocument();
    });
    expect(mockedFetchDevBlogList).toHaveBeenCalledWith({
      page: 2,
      limit: DEV_BLOG_PAGE_SIZE,
      tags: [],
      publishedFrom: undefined,
      publishedTo: undefined,
    });
  });
});
