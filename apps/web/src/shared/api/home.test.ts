import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./client', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPut: vi.fn(),
}));

vi.mock('../ui/toastBus', () => ({
  pushGlobalToast: vi.fn(),
}));

import { apiGet, apiPost, apiPut } from './client';
import { pushGlobalToast } from '../ui/toastBus';
import { getDraft, publishHome, previewHome, restoreHome, saveDraft } from './home';

beforeEach(() => {
  vi.mocked(apiGet).mockReset();
  vi.mocked(apiPost).mockReset();
  vi.mocked(apiPut).mockReset();
  vi.mocked(pushGlobalToast).mockReset();
});

describe('home api', () => {
  it('fetches draft state for provided slug and normalizes payload', async () => {
    vi.mocked(apiGet).mockResolvedValue({
      slug: 'landing',
      draft: {
        id: 'draft-1',
        slug: 'landing',
        version: '5',
        status: 'draft',
        data: { blocks: [] },
        created_at: '2025-10-10T10:00:00Z',
        updated_at: '2025-10-10T10:05:00Z',
      },
      published: {
        id: 'pub-1',
        slug: 'landing',
        version: 4,
        status: 'published',
        data: { blocks: [{ id: 'hero' }] },
        created_at: '2025-10-09T08:00:00Z',
        updated_at: '2025-10-09T08:30:00Z',
        published_at: '2025-10-09T08:30:00Z',
      },
      history: [
        {
          config_id: 'pub-1',
          version: 4,
          action: 'publish',
          actor: 'alice',
          actor_team: null,
          comment: 'Initial publish',
          created_at: '2025-10-09T08:30:00Z',
          published_at: '2025-10-09T08:30:00Z',
          is_current: true,
        },
      ],
    });

    const result = await getDraft({ slug: 'landing  ' });

    expect(apiGet).toHaveBeenCalledWith('/v1/admin/home?slug=landing', { signal: undefined });
    expect(result.slug).toBe('landing');
    expect(result.draft).toEqual({
      id: 'draft-1',
      slug: 'landing',
      version: 5,
      status: 'draft',
      data: { blocks: [] },
      created_at: '2025-10-10T10:00:00Z',
      updated_at: '2025-10-10T10:05:00Z',
      published_at: null,
      created_by: null,
      updated_by: null,
      draft_of: null,
    });
    expect(result.published?.status).toBe('published');
    expect(result.history).toEqual([
      {
        configId: 'pub-1',
        version: 4,
        action: 'publish',
        actor: 'alice',
        actorTeam: null,
        comment: 'Initial publish',
        createdAt: '2025-10-09T08:30:00Z',
        publishedAt: '2025-10-09T08:30:00Z',
        isCurrent: true,
      },
    ]);
  });

  it('saves draft and returns normalized snapshot', async () => {
    vi.mocked(apiPut).mockResolvedValue({
      id: 'draft-2',
      slug: 'main',
      version: 2,
      status: 'draft',
      data: { blocks: [] },
      created_at: '2025-10-10T11:00:00Z',
      updated_at: '2025-10-10T11:10:00Z',
      draft_of: 'pub-1',
    });

    const payload = { slug: ' main ', data: { blocks: [{ id: 'hero' }] } };
    const result = await saveDraft(payload);

    expect(apiPut).toHaveBeenCalledWith('/v1/admin/home', { slug: 'main', data: { blocks: [{ id: 'hero' }] } }, { signal: undefined });
    expect(result).toMatchObject({
      id: 'draft-2',
      slug: 'main',
      version: 2,
      status: 'draft',
    });
  });

  it('publishes draft and returns published snapshot', async () => {
    vi.mocked(apiPost).mockResolvedValue({
      slug: 'landing',
      published: {
        id: 'pub-2',
        slug: 'landing',
        version: 6,
        status: 'published',
        data: { blocks: [] },
        created_at: '2025-10-10T12:00:00Z',
        updated_at: '2025-10-10T12:01:00Z',
        published_at: '2025-10-10T12:01:00Z',
      },
    });

    const result = await publishHome({ slug: 'landing' });

    expect(apiPost).toHaveBeenCalledWith('/v1/admin/home/publish', { slug: 'landing', data: null }, { signal: undefined });
    expect(result).toEqual({
      slug: 'landing',
      published: {
        id: 'pub-2',
        slug: 'landing',
        version: 6,
        status: 'published',
        data: { blocks: [] },
        created_at: '2025-10-10T12:00:00Z',
        updated_at: '2025-10-10T12:01:00Z',
        published_at: '2025-10-10T12:01:00Z',
        created_by: null,
        updated_by: null,
        draft_of: null,
      },
    });
  });

  it('includes trimmed comment when publishing', async () => {
    vi.mocked(apiPost).mockResolvedValue({
      slug: 'main',
      published: {
        id: 'pub',
        slug: 'main',
        version: 2,
        status: 'published',
        data: {},
        created_at: '2025-10-10T12:00:00Z',
        updated_at: '2025-10-10T12:00:30Z',
        published_at: '2025-10-10T12:00:30Z',
      },
    });

    await publishHome({ slug: 'main', comment: '  ship it  ' });

    expect(apiPost).toHaveBeenCalledWith('/v1/admin/home/publish', { slug: 'main', data: null, comment: 'ship it' }, { signal: undefined });
  });

  it('previews configuration and falls back to empty payload when missing', async () => {
    vi.mocked(apiPost).mockResolvedValueOnce({
      slug: 'main',
      payload: { slug: 'main', blocks: [{ id: 'hero' }] },
    });

    const preview = await previewHome({ slug: 'main', data: { blocks: [] } });

    expect(apiPost).toHaveBeenCalledWith('/v1/admin/home/preview', { slug: 'main', data: { blocks: [] } }, { signal: undefined });
    expect(preview).toEqual({ slug: 'main', payload: { slug: 'main', blocks: [{ id: 'hero' }] } });

    vi.mocked(apiPost).mockResolvedValueOnce({ slug: 'main' });
    const fallback = await previewHome({});
    expect(fallback.payload).toEqual({});
  });

  it('restores configuration version and normalizes response', async () => {
    vi.mocked(apiPost).mockResolvedValue({
      slug: 'main',
      draft: {
        id: 'draft-3',
        slug: 'main',
        version: 7,
        status: 'draft',
        data: { blocks: [] },
        created_at: '2025-10-10T13:00:00Z',
        updated_at: '2025-10-10T13:05:00Z',
      },
    });

    const result = await restoreHome(7, { slug: 'main' });

    expect(apiPost).toHaveBeenCalledWith('/v1/admin/home/restore/7', { slug: 'main', data: null }, { signal: undefined });
    expect(result.draft.version).toBe(7);
  });

  it('sends trimmed comment when restoring version', async () => {
    vi.mocked(apiPost).mockResolvedValue({
      slug: 'main',
      draft: {
        id: 'draft-5',
        slug: 'main',
        version: 5,
        status: 'draft',
        data: { blocks: [] },
        created_at: '2025-10-10T14:00:00Z',
        updated_at: '2025-10-10T14:05:00Z',
      },
    });

    await restoreHome(5, { slug: 'main', comment: '  restore ' });

    expect(apiPost).toHaveBeenCalledWith('/v1/admin/home/restore/5', { slug: 'main', data: null, comment: 'restore' }, { signal: undefined });
  });

  it('raises toast and rethrows on forbidden error', async () => {
    const error = new Error('Forbidden');
    (error as any).status = 403;
    (error as any).body = '"insufficient_permissions"';
    vi.mocked(apiGet).mockRejectedValue(error);

    await expect(getDraft()).rejects.toThrow('Forbidden');
    expect(pushGlobalToast).toHaveBeenCalledWith({ intent: 'error', description: 'Недостаточно прав' });
  });

  it('emits detailed toast for validation errors with duplicates', async () => {
    const error = new Error('Invalid');
    (error as any).status = 422;
    (error as any).body = JSON.stringify({
      code: 'home_config_duplicate_block_ids',
      details: ['hero', 'hero'],
    });
    vi.mocked(apiPut).mockRejectedValue(error);

    await expect(saveDraft({ slug: 'main', data: {} })).rejects.toThrow('Invalid');
    expect(pushGlobalToast).toHaveBeenCalledWith({
      intent: 'error',
      description: 'Идентификаторы блоков должны быть уникальными: hero, hero',
    });
  });

  it('falls back to default toast when response is malformed', async () => {
    vi.mocked(apiPost).mockResolvedValue({ slug: 'main', published: null });

    await expect(publishHome({ slug: 'main' })).rejects.toThrow('home_invalid_publish_response');
    expect(pushGlobalToast).toHaveBeenCalledWith({ intent: 'error', description: 'Некорректный ответ сервера. Попробуйте позже.' });
  });

  it('does not call API when restore version is invalid', async () => {
    await expect(restoreHome(NaN as any, { slug: 'main' })).rejects.toThrow('home_invalid_restore_version');
    expect(apiPost).not.toHaveBeenCalled();
    expect(pushGlobalToast).not.toHaveBeenCalled();
  });

  it('shows session lost toast on unauthorized error', async () => {
    const error = new Error('Unauthorized');
    (error as any).status = 401;
    vi.mocked(apiGet).mockRejectedValue(error);

    await expect(getDraft()).rejects.toThrow('Unauthorized');
    expect(pushGlobalToast).toHaveBeenCalledWith({ intent: 'error', description: 'Сессия истекла. Пожалуйста, войдите снова.' });
  });
});

