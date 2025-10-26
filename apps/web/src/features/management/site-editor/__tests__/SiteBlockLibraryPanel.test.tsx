import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SiteBlockLibraryPanel } from '../components/SiteBlockLibraryPanel';
import { HomeEditorContext } from '../../home/HomeEditorContext';
import type { HomeEditorContextValue, HomeBlock, HomeDraftData, HomeDraftSnapshot } from '../../home/types';
import type { ValidationSummary } from '../../home/validation';

vi.mock('../dataAdapters/useBlockPreview', () => ({
  useBlockPreview: () => ({
    data: {
      items: [
        { title: 'Sample item 1', subtitle: 'Subtitle 1', href: '/sample-1' },
        { title: 'Sample item 2', subtitle: 'Subtitle 2', href: '/sample-2' },
      ],
      locale: 'ru',
      fetchedAt: '2025-10-25T12:00:00Z',
      source: 'mock',
      meta: {},
    },
    loading: false,
    error: null,
  }),
}));

function makeContext(overrides: Partial<HomeEditorContextValue> = {}): HomeEditorContextValue {
  const data: HomeDraftData = overrides.data ?? { blocks: [] };
  const validation: ValidationSummary = overrides.validation ?? { valid: true, general: [], blocks: {} };
  const snapshot: HomeDraftSnapshot = overrides.snapshot ?? { version: null, updatedAt: null, publishedAt: null };

  return {
    loading: false,
    data,
    setData: overrides.setData ?? vi.fn(),
    setBlocks: overrides.setBlocks ?? vi.fn(),
    selectBlock: overrides.selectBlock ?? vi.fn(),
    selectedBlockId: overrides.selectedBlockId ?? null,
    dirty: overrides.dirty ?? false,
    saving: overrides.saving ?? false,
    savingError: overrides.savingError ?? null,
    lastSavedAt: overrides.lastSavedAt ?? null,
    loadDraft: overrides.loadDraft ?? vi.fn(() => Promise.resolve()),
    saveDraft: overrides.saveDraft ?? vi.fn(() => Promise.resolve()),
    snapshot,
    slug: overrides.slug ?? '/',
    history: overrides.history ?? [],
    publishing: overrides.publishing ?? false,
    publishDraft: overrides.publishDraft ?? vi.fn(() => Promise.resolve()),
    restoreVersion: overrides.restoreVersion ?? vi.fn(() => Promise.resolve()),
    restoringVersion: overrides.restoringVersion ?? null,
    validation,
    revalidate: overrides.revalidate ?? vi.fn(() => validation),
  };
}

function renderPanel(overrides: Partial<HomeEditorContextValue> = {}) {
  const contextValue = makeContext(overrides);
  const user = userEvent.setup();
  render(
    <HomeEditorContext.Provider value={contextValue}>
      <SiteBlockLibraryPanel />
    </HomeEditorContext.Provider>,
  );
  return { contextValue, user };
}

describe('SiteBlockLibraryPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('добавляет доступный блок и выбирает его', async () => {
    const setBlocks = vi.fn();
    const selectBlock = vi.fn();
    const { user, contextValue } = renderPanel({
      setBlocks,
      selectBlock,
    });

    const addHeroButton = await screen.findByRole('button', { name: 'Добавить блок Hero-блок' });
    await user.click(addHeroButton);

    expect(setBlocks).toHaveBeenCalledTimes(1);
    const updatedBlocks = setBlocks.mock.calls[0][0] as HomeBlock[];
    expect(Array.isArray(updatedBlocks)).toBe(true);
    expect(updatedBlocks.some((block) => block.type === 'hero')).toBe(true);

    expect(selectBlock).toHaveBeenCalledTimes(1);
    expect(selectBlock.mock.calls[0][0]).toBe('hero-1');

    // исходный список блоков в контексте не изменяется автоматически
    expect(contextValue.data.blocks).toHaveLength(0);
  });

  it('фильтрует блоки по поиску и сбрасывает фильтры', async () => {
    const { user } = renderPanel();

    const searchInput = screen.getByPlaceholderText('Поиск по названию, источнику или владельцу');
    await user.type(searchInput, 'Dev');

    const devBlogButton = await screen.findByRole('button', { name: 'Добавить блок Dev Blog' });
    expect(devBlogButton).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Добавить блок Hero-блок' })).toBeNull();

    const resetButton = await screen.findByRole('button', { name: 'Сбросить' });
    await user.click(resetButton);

    expect(await screen.findByRole('button', { name: 'Добавить блок Hero-блок' })).toBeInTheDocument();
  });

  it('делает недоступными блоки в разработке', async () => {
    renderPanel();

    const upcomingButton = await screen.findByRole('button', {
      name: 'Блок Глобальный хедер скоро будет доступен',
    });

    expect(upcomingButton).toBeDisabled();
  });
});

