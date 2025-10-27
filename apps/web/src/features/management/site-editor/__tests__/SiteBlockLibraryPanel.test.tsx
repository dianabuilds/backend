import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { SiteBlockLibraryPanel } from '../components/SiteBlockLibraryPanel';
import { HomeEditorContext } from '../../home/HomeEditorContext';
import type { HomeEditorContextValue, HomeBlock, HomeDraftData, HomeDraftSnapshot } from '../../home/types';
import type { ValidationSummary } from '../../home/validation';



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
    <MemoryRouter>
      <HomeEditorContext.Provider value={contextValue}>
        <SiteBlockLibraryPanel />
      </HomeEditorContext.Provider>
    </MemoryRouter>,
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

    const addHeroButton = await screen.findByRole('button', { name: /Hero-блок/ });
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

    const searchInput = screen.getByPlaceholderText('Поиск по названию или описанию');
    await user.type(searchInput, 'Dev');

    const devBlogButton = await screen.findByRole('button', { name: /Dev Blog/ });
    expect(devBlogButton).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Hero-блок/ })).toBeNull();

    await user.clear(searchInput);

    expect(await screen.findByRole('button', { name: /Hero-блок/ })).toBeInTheDocument();
  });

});

