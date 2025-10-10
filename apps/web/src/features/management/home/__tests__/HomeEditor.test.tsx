import React from 'react';
import { describe, it, beforeEach, expect, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { ToastProvider } from '@ui';
import HomeEditor from '../components/HomeEditor';
import { getDraft, saveDraft, previewHome } from '@shared/api/home';
import type { HomeConfigSnapshot } from '@shared/types/home';

vi.mock('@shared/api/home', () => ({
  getDraft: vi.fn(),
  saveDraft: vi.fn(),
  publishHome: vi.fn(),
  previewHome: vi.fn(),
  restoreHome: vi.fn(),
}));

const mockedGetDraft = vi.mocked(getDraft);
const mockedSaveDraft = vi.mocked(saveDraft);
const mockedPreviewHome = vi.mocked(previewHome);

function makeSnapshot(version: number, blocks: any[]): HomeConfigSnapshot {
  const timestamp = `2025-10-10T10:0${version}:00Z`;
  return {
    id: `draft-${version}`,
    slug: 'main',
    version,
    status: 'draft',
    data: { blocks },
    created_at: timestamp,
    updated_at: timestamp,
    published_at: null,
    created_by: null,
    updated_by: null,
    draft_of: null,
  };
}

async function renderHomeEditor() {
  const user = userEvent.setup();
  render(
    <MemoryRouter>
      <ToastProvider>
        <HomeEditor />
      </ToastProvider>
    </MemoryRouter>,
  );
  await screen.findByText('Библиотека блоков');
  return user;
}

describe('HomeEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedGetDraft.mockResolvedValue({
      slug: 'main',
      draft: makeSnapshot(1, []),
      published: null,
      history: [],
    });
    mockedSaveDraft.mockResolvedValue(makeSnapshot(2, []));
    mockedPreviewHome.mockResolvedValue({ slug: 'main', payload: { blocks: [], fallbacks: [], meta: {} } });
  });

  it('allows adding hero block from library', async () => {
    const user = await renderHomeEditor();

    await user.click(await screen.findByRole('button', { name: /Hero-блок/i }));

    const cards = await screen.findAllByTestId(/home-block-/);
    expect(cards).toHaveLength(1);
  });

  it('updates block title via inspector form', async () => {
    const user = await renderHomeEditor();
    await user.click(await screen.findByRole('button', { name: /Hero-блок/i }));

    const titleInput = await screen.findByPlaceholderText('Например, Главный блок');
    await user.clear(titleInput);
    await user.type(titleInput, 'Новый заголовок');

    const [blockCard] = await screen.findAllByTestId(/home-block-/);
    expect(within(blockCard).getByText('Новый заголовок')).toBeInTheDocument();
  });

  it('marks block as disabled when toggled off', async () => {
    const user = await renderHomeEditor();
    await user.click(await screen.findByRole('button', { name: /Hero-блок/i }));

    const toggle = await screen.findByRole('checkbox', { name: /Включить или выключить блок/i });
    await user.click(toggle);

    const [blockCard] = await screen.findAllByTestId(/home-block-/);
    expect(within(blockCard).getByText('Отключён')).toBeInTheDocument();
  });

  it('removes block from canvas', async () => {
    const user = await renderHomeEditor();
    await user.click(await screen.findByRole('button', { name: /Hero-блок/i }));

    const removeButton = await screen.findByRole('button', { name: 'Удалить блок' });
    await user.click(removeButton);

    expect(screen.queryAllByTestId(/home-block-/)).toHaveLength(0);
    expect(screen.getByText(/Выберите блок/)).toBeInTheDocument();
  });
});

