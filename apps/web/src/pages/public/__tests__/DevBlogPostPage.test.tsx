import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import DevBlogPostPage from '../DevBlogPostPage';
import { buildDevBlogPostKey } from '../DevBlogPostPage.shared';
import { InitialDataProvider } from '@shared/ssr/InitialDataContext';
import { fetchDevBlogPost } from '@shared/api/devBlog';
import type { DevBlogDetailResponse } from '@shared/types/devBlog';

vi.mock('@shared/api/devBlog', () => ({
  fetchDevBlogList: vi.fn(),
  fetchDevBlogPost: vi.fn(),
}));

const mockedFetchDevBlogPost = vi.mocked(fetchDevBlogPost);

const detailResponse: DevBlogDetailResponse = {
  post: {
    id: 1,
    slug: 'first-post',
    title: 'Первый пост',
    summary: 'Краткий обзор последних обновлений.',
    coverUrl: null,
    publishAt: '2025-10-10T10:00:00Z',
    updatedAt: '2025-10-10T12:00:00Z',
    author: { id: '42', name: 'Команда' },
    content: '<p>Контент поста</p>',
    status: 'published',
    isPublic: true,
    tags: ['updates', 'engineering'],
  },
  prev: null,
  next: {
    id: 2,
    slug: 'next-post',
    title: 'Следующий пост',
    summary: null,
    coverUrl: null,
    publishAt: '2025-10-12T10:00:00Z',
    updatedAt: '2025-10-12T10:00:00Z',
    author: { id: '11', name: 'Отдел разработки' },
  },
};

function renderPostPage(data: Record<string, unknown> | null = null, slug = 'first-post') {
  return render(
    <HelmetProvider>
      <InitialDataProvider data={data ?? undefined}>
        <MemoryRouter initialEntries={[`/dev-blog/${slug}`]}>
          <Routes>
            <Route path="/dev-blog/:slug" element={<DevBlogPostPage />} />
          </Routes>
        </MemoryRouter>
      </InitialDataProvider>
    </HelmetProvider>,
  );
}

beforeEach(() => {
  mockedFetchDevBlogPost.mockReset();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('DevBlogPostPage', () => {
  it('renders cached post data without fetching', () => {
    const key = buildDevBlogPostKey('first-post');
    if (!key) throw new Error('key not generated');
    renderPostPage({ [key]: detailResponse });

    expect(screen.getByText('Первый пост')).toBeInTheDocument();
    expect(screen.getByText('Поделиться постом')).toBeInTheDocument();
    expect(screen.getAllByText('Следующий пост').length).toBeGreaterThanOrEqual(1);
    expect(mockedFetchDevBlogPost).not.toHaveBeenCalled();
  });

  it('renders API error state when request fails', async () => {
    mockedFetchDevBlogPost.mockResolvedValue({ data: null, status: 404, error: 'not_found' });

    renderPostPage(null, 'missing-post');

    await waitFor(() => {
      expect(screen.getByText('not_found')).toBeInTheDocument();
    });
    expect(mockedFetchDevBlogPost).toHaveBeenCalledWith('missing-post');
  });
});
