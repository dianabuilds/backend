import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { HomeBlocks } from '@features/public/home';
import type { HomeBlockItem, HomeBlockPayload } from '@shared/types/homePublic';
import { rumEvent } from '@shared/rum';

vi.mock('@shared/rum', () => ({
  rumEvent: vi.fn(),
}));

const mockedRumEvent = vi.mocked(rumEvent);

function renderBlocks(blocks: HomeBlockPayload[]) {
  return render(
    <MemoryRouter>
      <HomeBlocks blocks={blocks} />
    </MemoryRouter>,
  );
}

function createBlock(overrides: Partial<HomeBlockPayload> = {}): HomeBlockPayload {
  return {
    id: overrides.id ?? `block-${Math.random().toString(16).slice(2)}`,
    type: overrides.type ?? 'hero',
    title: overrides.title ?? 'Sample block',
    enabled: overrides.enabled ?? true,
    slots: overrides.slots ?? null,
    layout: overrides.layout ?? null,
    items: overrides.items ?? [],
    dataSource: overrides.dataSource ?? null,
  };
}

beforeEach(() => {
  mockedRumEvent.mockReset();
});

describe('HomeBlocks', () => {
  it('renders hero block with headline and CTA', () => {
    const block = createBlock({
      id: 'hero-block',
      type: 'hero',
      slots: {
        headline: 'Главное событие',
        subheadline: 'Описание блока',
        cta: { label: 'Подробнее', href: '/more' },
        media: 'https://cdn.caves.world/hero.jpg',
      },
    });

    renderBlocks([block]);

    expect(screen.getByRole('heading', { level: 1, name: 'Главное событие' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Подробнее' })).toHaveAttribute('href', '/more');
    const heroImage = screen.getByRole('img', { name: 'Главное событие' });
    expect(heroImage).toHaveAttribute('loading', 'eager');
    expect(heroImage).toHaveAttribute('fetchpriority', 'high');
    expect(heroImage).toHaveAttribute('sizes', '(min-width: 1024px) 36rem, 100vw');
  });

  it('uses lazy loading for secondary hero media', () => {
    const blocks = [
      createBlock({
        id: 'hero-primary',
        type: 'hero',
        slots: { headline: 'Первый блок', media: 'https://cdn.caves.world/hero-primary.jpg' },
      }),
      createBlock({
        id: 'hero-secondary',
        type: 'hero',
        slots: { headline: 'Второй блок', media: 'https://cdn.caves.world/hero-secondary.jpg' },
      }),
    ];

    renderBlocks(blocks);

    const secondaryImage = screen.getByRole('img', { name: 'Второй блок' });
    expect(secondaryImage).toHaveAttribute('loading', 'lazy');
    expect(secondaryImage.getAttribute('fetchpriority')).toBeNull();
    expect(secondaryImage.getAttribute('sizes')).toBeNull();
  });

  it('respects dataSource limit for dev blog list', () => {
    const items: HomeBlockItem[] = [
      { id: '1', slug: 'first', title: 'Первый пост', publishAt: '2025-10-01T00:00:00Z' },
      { id: '2', slug: 'second', title: 'Второй пост', publishAt: '2025-10-02T00:00:00Z' },
      { id: '3', slug: 'third', title: 'Третий пост', publishAt: '2025-10-03T00:00:00Z' },
    ];
    const block = createBlock({
      id: 'dev-blog',
      type: 'dev_blog_list',
      title: 'Dev Blog',
      items,
      dataSource: {
        mode: 'auto',
        entity: 'dev_blog',
        filter: { limit: 2 },
        items: null,
      },
    });

    renderBlocks([block]);

    expect(screen.getByText('Первый пост')).toBeInTheDocument();
    expect(screen.getByText('Второй пост')).toBeInTheDocument();
    expect(screen.queryByText('Третий пост')).not.toBeInTheDocument();
  });

  it('shows empty state for carousel blocks without items', () => {
    const block = createBlock({
      id: 'carousel',
      type: 'quests_carousel',
      title: 'Квесты',
      items: [],
    });

    renderBlocks([block]);

    expect(screen.getByText('Для этого раздела пока нет материалов.')).toBeInTheDocument();
  });

  it('renders fallback for unknown block type', () => {
    const block = createBlock({ id: 'unknown', type: 'mystery' });

    renderBlocks([block]);

    expect(screen.getByText(/пока не поддерживается/i)).toBeInTheDocument();
  });

  it('emits analytics for visible blocks with 1-based positions', async () => {
    const hero = createBlock({
      id: 'hero-analytics',
      type: 'hero',
      slots: { headline: 'Analytics Hero' },
    });
    const devBlog = createBlock({ id: 'dev-analytics', type: 'dev_blog_list', items: [] });

    renderBlocks([hero, devBlog]);

    await waitFor(() => expect(mockedRumEvent).toHaveBeenCalledTimes(2));
    expect(mockedRumEvent.mock.calls[0]).toEqual([
      'home.block_rendered',
      { type: 'hero', position: 1 },
    ]);
    expect(mockedRumEvent.mock.calls[1]).toEqual([
      'home.block_rendered',
      { type: 'dev_blog_list', position: 2 },
    ]);
  });

  it('skips disabled blocks and does not emit analytics', async () => {
    const enabled = createBlock({
      id: 'enabled-block',
      type: 'hero',
      slots: { headline: 'Видимый блок' },
    });
    const disabled = createBlock({
      id: 'disabled-block',
      type: 'hero',
      enabled: false,
      slots: { headline: 'Скрытый блок' },
    });

    renderBlocks([enabled, disabled]);

    expect(screen.getByText('Видимый блок')).toBeInTheDocument();
    expect(screen.queryByText('Скрытый блок')).not.toBeInTheDocument();
    await waitFor(() => expect(mockedRumEvent).toHaveBeenCalledTimes(1));
  });
});
