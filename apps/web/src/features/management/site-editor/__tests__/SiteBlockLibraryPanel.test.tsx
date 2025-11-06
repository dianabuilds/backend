import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

import { SiteBlockLibraryPanel } from '../components/SiteBlockLibraryPanel';
import { HomeEditorContext } from '../../home/HomeEditorContext';
import { listBlockDefinitions } from '../../home/blockDefinitions';
import type { HomeEditorContextValue, HomeBlock, HomeDraftData, HomeDraftSnapshot } from '../../home/types';
import type { ValidationSummary } from '../../home/validation';
import type { SitePageAttachedBlock } from '@shared/types/management';

const BLOCK_DEFINITIONS = listBlockDefinitions();

function makeContext(overrides: Partial<HomeEditorContextValue> = {}): HomeEditorContextValue {
  const data: HomeDraftData = overrides.data ?? { blocks: [] };
  const validation: ValidationSummary = overrides.validation ?? { valid: true, general: [], blocks: {} };
  const snapshot: HomeDraftSnapshot = overrides.snapshot ?? { version: null, updatedAt: null, publishedAt: null };
  const sharedAssignments = overrides.sharedAssignments ?? { header: null, footer: null };
  const sharedBindings: Record<string, SitePageAttachedBlock | null> =
    overrides.sharedBindings ?? { header: null, footer: null };

  return {
    page: overrides.page ?? null,
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
    sharedBindings,
    sharedAssignments,
    setSharedAssignment: overrides.setSharedAssignment ?? vi.fn(),
    clearSharedAssignment: overrides.clearSharedAssignment ?? vi.fn(),
    updateSharedBindingInfo: overrides.updateSharedBindingInfo ?? vi.fn(),
    assignSharedBinding: overrides.assignSharedBinding ?? vi.fn(() => Promise.resolve()),
    removeSharedBinding: overrides.removeSharedBinding ?? vi.fn(() => Promise.resolve()),
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
  it('отображает статичный список и добавляет выбранный блок', async () => {
    const setBlocks = vi.fn();
    const selectBlock = vi.fn();
    const { user, contextValue } = renderPanel({ setBlocks, selectBlock });

    const heroDefinition = BLOCK_DEFINITIONS.find((definition) => definition.type === 'hero');
    expect(heroDefinition).toBeDefined();
    const heroButton = screen.getByRole('button', { name: new RegExp(heroDefinition!.label, 'i') });
    await user.click(heroButton);

    expect(setBlocks).toHaveBeenCalledTimes(1);
    const updatedBlocks = setBlocks.mock.calls[0][0] as HomeBlock[];
    expect(updatedBlocks.some((block) => block.type === heroDefinition!.type)).toBe(true);

    expect(selectBlock).toHaveBeenCalledTimes(1);
    expect(contextValue.data.blocks).toHaveLength(0);
  });

  it('фильтрует список по поиску', async () => {
    const { user } = renderPanel();
    const searchInput = screen.getByPlaceholderText('Поиск по названию или описанию');

    await user.type(searchInput, 'dev');

    const devDefinition = BLOCK_DEFINITIONS.find((definition) => definition.type === 'dev_blog_list');
    expect(devDefinition).toBeDefined();
    expect(screen.getByRole('button', { name: new RegExp(devDefinition!.label, 'i') })).toBeInTheDocument();

    const heroDefinition = BLOCK_DEFINITIONS.find((definition) => definition.type === 'hero');
    expect(heroDefinition).toBeDefined();
    expect(screen.queryByRole('button', { name: new RegExp(heroDefinition!.label, 'i') })).toBeNull();

    await user.clear(searchInput);
    expect(screen.getByRole('button', { name: new RegExp(heroDefinition!.label, 'i') })).toBeInTheDocument();
  });
});

