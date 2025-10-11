import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import HomePage from '../HomePage';
import { HelmetProvider } from 'react-helmet-async';
import { buildHomeCacheKey } from '../HomePage.shared';
import { InitialDataProvider } from '@shared/ssr/InitialDataContext';
import { fetchPublicHome } from '@shared/api/publicHome';
import type { HomeResponse } from '@shared/types/homePublic';
import { rumEvent } from '@shared/rum';
import { reportFeatureError } from '@shared/utils/sentry';

vi.mock('@shared/api/publicHome', () => ({
  fetchPublicHome: vi.fn(),
}));
vi.mock('@shared/rum', () => ({
  rumEvent: vi.fn(),
}));
vi.mock('@shared/utils/sentry', () => ({
  reportFeatureError: vi.fn(),
}));

const mockedFetchPublicHome = vi.mocked(fetchPublicHome);
const mockedRumEvent = vi.mocked(rumEvent);
const mockedReportFeatureError = vi.mocked(reportFeatureError);

const sampleHome: HomeResponse = {
  slug: 'main',
  version: 1,
  updatedAt: '2025-10-10T10:00:00Z',
  publishedAt: '2025-10-10T10:00:00Z',
  generatedAt: '2025-10-10T10:00:00Z',
  blocks: [
    {
      id: 'hero-1',
      type: 'hero',
      title: 'Hero',
      enabled: true,
      slots: { headline: 'Привет, герой!', media: 'https://cdn.caves.world/hero.jpg' },
      layout: null,
      items: [],
      dataSource: null,
    },
  ],
  meta: {},
  fallbacks: [],
};

function renderHomePage(data: Record<string, unknown> | null = null) {
  return render(
    <HelmetProvider>
      <InitialDataProvider data={data ?? undefined}>
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      </InitialDataProvider>
    </HelmetProvider>,
  );
}

beforeEach(() => {
  mockedFetchPublicHome.mockReset();
  mockedRumEvent.mockReset();
  mockedReportFeatureError.mockReset();
  window.history.replaceState({}, '', '/');
});

afterEach(() => {
  vi.clearAllMocks();
  document.head.innerHTML = '';
});

describe('HomePage', () => {
  it('отрисовывает блоки из начальных данных и отправляет метрики', async () => {
    const key = buildHomeCacheKey('main');
    renderHomePage({ [key]: sampleHome });

    const heroHeading = await screen.findByText('Привет, герой!');
    expect(heroHeading).toBeInTheDocument();

    await waitFor(() => {
      expect(mockedRumEvent.mock.calls.some(([event]) => event === 'home.load_success')).toBe(true);
    });

    const startCall = mockedRumEvent.mock.calls.find(([event]) => event === 'home.load_start');
    expect(startCall).toBeDefined();
    expect(startCall?.[1]).toMatchObject({ slug: 'main', hasCachedData: true });
  });

  it('preloads hero media when available', async () => {
    const key = buildHomeCacheKey('main');
    renderHomePage({ [key]: sampleHome });

    await waitFor(() => {
      expect(document.head.querySelector('link[rel="preload"][as="image"]')).not.toBeNull();
    });

    const preloadLink = document.head.querySelector('link[rel="preload"][as="image"]');
    expect(preloadLink?.getAttribute('href')).toBe('https://cdn.caves.world/hero.jpg');
    expect(preloadLink?.getAttribute('fetchpriority')).toBe('high');
  });

  it('показывает fallback и логирует ошибку при неудачном запросе', async () => {
    mockedFetchPublicHome.mockResolvedValue({ data: null, status: 503, error: 'boom', etag: null });

    renderHomePage();

    await waitFor(() => {
      expect(screen.getByText('boom')).toBeInTheDocument();
    });

    expect(mockedFetchPublicHome).toHaveBeenCalledTimes(1);
    expect(mockedReportFeatureError).toHaveBeenCalled();
    const errorCall = mockedRumEvent.mock.calls.find(([event]) => event === 'home.load_error');
    expect(errorCall).toBeDefined();
    expect(errorCall?.[1]).toMatchObject({ slug: 'main', status: 503 });
  });

  it('повторяет загрузку после нажатия кнопки «Обновить»', async () => {
    mockedFetchPublicHome
      .mockResolvedValueOnce({ data: null, status: 500, error: 'fail', etag: null })
      .mockResolvedValueOnce({ data: sampleHome, status: 200, etag: 'etag-123' });

    renderHomePage();

    await waitFor(() => {
      expect(screen.getByText('fail')).toBeInTheDocument();
    });

    mockedRumEvent.mockClear();

    const refreshButton = screen.getByRole('button', { name: 'Обновить' });
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(mockedFetchPublicHome).toHaveBeenCalledTimes(2);
    });

    await waitFor(() => {
      expect(screen.getByText('Привет, герой!')).toBeInTheDocument();
    });

    expect(mockedRumEvent.mock.calls.some(([event]) => event === 'home.load_success')).toBe(true);
  });

  it('формирует canonical и hreflang на основе мета-конфигурации', async () => {
    const key = buildHomeCacheKey('main');
    const metaHome: HomeResponse = {
      ...sampleHome,
      meta: {
        origin: 'https://preview.caves.world',
        title_ru: 'Главная страница',
        title_en: 'Homepage',
        description: { ru: 'Описание для главной', en: 'Homepage description' },
        canonical: '/home',
        alternates: {
          ru: '/home',
          en: 'https://preview.caves.world/en/home',
        },
        ogImage: '/cover.png',
        siteName: 'Caves Preview',
      },
    };
    renderHomePage({ [key]: metaHome });

    await waitFor(() => {
      expect(document.head.querySelector('link[rel="canonical"]')).not.toBeNull();
    });

    const canonical = document.head.querySelector('link[rel="canonical"]');
    expect(canonical?.getAttribute('href')).toBe('https://preview.caves.world/home');

    const alternates = Array.from(document.head.querySelectorAll('link[rel="alternate"]')).map((node) => ({
      hreflang: node.getAttribute('hreflang'),
      href: node.getAttribute('href'),
    }));
    expect(alternates).toEqual(
      expect.arrayContaining([
        { hreflang: 'ru', href: 'https://preview.caves.world/home' },
        { hreflang: 'en', href: 'https://preview.caves.world/en/home' },
        { hreflang: 'x-default', href: 'https://preview.caves.world/home' },
      ]),
    );

    const ogSiteName = document.head.querySelector('meta[property="og:site_name"]');
    expect(ogSiteName?.getAttribute('content')).toBe('Caves Preview');

    const styleTag = document.head.querySelector('#home-critical-css');
    expect(styleTag?.textContent).toContain('main[data-home-root]');
  });
});
