import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./client', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}));

import { apiDelete, apiGet, apiPatch, apiPost } from './client';
import {
  fetchModerationUsers,
  fetchModerationUserDetail,
  updateModerationUserRoles,
  createModerationUserSanction,
  createModerationUserNote,
} from './moderation/users';
import { fetchModerationOverview } from './moderation/overview';
import {
  createModerationAIRule,
  deleteModerationAIRule,
  fetchModerationAIRules,
  updateModerationAIRule,
} from './moderation/ai-rules';

beforeEach(() => {
  vi.mocked(apiGet).mockReset();
  vi.mocked(apiPost).mockReset();
  vi.mocked(apiPatch).mockReset();
  vi.mocked(apiDelete).mockReset();
});

describe('moderation api', () => {
  it('normalizes moderation users list and pagination metadata', async () => {
    vi.mocked(apiGet).mockResolvedValue({
      items: [
        {
          id: 'u-1',
          username: 'Alice',
          email: 'alice@example.com',
          roles: ['ADMIN', 'support'],
          complaints_count: '4',
          notesCount: 2,
          sanction_count: '1',
          last_seen_at: '2025-10-01T10:00:00Z',
          meta: { risk_label: 'high' },
        },
        {
          id: null,
          username: null,
          roles: null,
        },
      ],
      next_cursor: 'cursor-2',
      total: '10',
      meta: { source: 'test' },
    });

    const result = await fetchModerationUsers({ limit: 10, status: 'active', role: 'moderator', search: ' test ' });

    expect(apiGet).toHaveBeenCalledWith('/api/moderation/users?limit=10&status=active&role=moderator&q=test', {
      signal: undefined,
    });
    expect(result.items).toHaveLength(1);
    expect(result.items[0]).toMatchObject({
      id: 'u-1',
      username: 'Alice',
      roles: ['admin', 'support'],
      complaints_count: 4,
      notes_count: 2,
      sanction_count: 1,
      meta: { risk_label: 'high' },
    });
    expect(result.nextCursor).toBe('cursor-2');
    expect(result.total).toBe(10);
    expect(result.meta).toEqual({ source: 'test' });
  });

  it('fetches moderation user detail with trimmed id', async () => {
    vi.mocked(apiGet).mockResolvedValue({
      id: 'user-1',
      username: 'User',
      sanctions: [],
      reports: [],
      tickets: [],
      notes: [],
    });

    const detail = await fetchModerationUserDetail(' user-1 ');

    expect(apiGet).toHaveBeenCalledWith('/api/moderation/users/user-1', { signal: undefined });
    expect(detail.id).toBe('user-1');
  });

  it('updates user roles and creates sanction and note', async () => {
    await updateModerationUserRoles(' user-2 ', { add: ['Admin'], remove: ['User'] });
    expect(apiPost).toHaveBeenCalledWith('/api/moderation/users/user-2/roles', { add: ['Admin'], remove: ['User'] }, {
      signal: undefined,
    });

    await createModerationUserSanction('user-3', { type: 'ban', reason: 'spam', duration_hours: 24 });
    expect(apiPost).toHaveBeenCalledWith(
      '/api/moderation/users/user-3/sanctions',
      { type: 'ban', reason: 'spam', duration_hours: 24 },
      { signal: undefined },
    );

    await createModerationUserNote('user-4', { text: 'hello', pinned: true });
    expect(apiPost).toHaveBeenCalledWith(
      '/api/moderation/users/user-4/notes',
      { text: 'hello', pinned: true },
      { signal: undefined },
    );
  });

  it('normalizes moderation overview payload', async () => {
    vi.mocked(apiGet).mockResolvedValue({
      complaints: { open: '5', resolved: 2 },
      tickets: { backlog: '3' },
      content_queues: { urgent: 7 },
      cards: [
        {
          id: 'sla',
          title: 'SLA breaches',
          value: '4',
          delta: '+2',
          trend: 'up',
          description: 'Breaches in the last 24h',
          actions: [{ label: 'Open incidents', to: '/incidents' }],
        },
      ],
      charts: [
        {
          id: 'volume',
          title: 'Queue volume',
          type: 'bar',
          series: [{ name: 'Urgent', data: [1, 2, 3] }],
          options: { stacked: true },
        },
      ],
      last_sanctions: [
        { id: 's-1', type: 'ban', status: 'active', issued_at: '2025-10-01T00:00:00Z' },
      ],
    });

    const result = await fetchModerationOverview();

    expect(apiGet).toHaveBeenCalledWith('/api/moderation/overview', { signal: undefined });
    expect(result.complaints).toEqual({ open: 5, resolved: 2 });
    expect(result.tickets).toEqual({ backlog: 3 });
    expect(result.contentQueues).toEqual({ urgent: 7 });
    expect(result.cards[0]).toMatchObject({ id: 'sla', title: 'SLA breaches', value: '4', delta: '+2', trend: 'up' });
    expect(result.charts[0]).toMatchObject({ id: 'volume', type: 'bar' });
    expect(result.lastSanctions[0]).toMatchObject({ id: 's-1', type: 'ban', status: 'active' });
  });

  it('normalizes AI rules list and computes hasNext flag', async () => {
    vi.mocked(apiGet).mockResolvedValue({
      items: [
        {
          id: 'r-1',
          category: 'toxicity',
          enabled: 'true',
          default_action: 'flag',
          threshold: '0.8',
          updated_by: 'alice',
          updated_at: '2025-10-02T10:00:00Z',
        },
      ],
      total: '50',
    });

    const result = await fetchModerationAIRules({ limit: 20, offset: 20 });

    expect(apiGet).toHaveBeenCalledWith('/api/moderation/ai-rules?limit=20&offset=20', { signal: undefined });
    expect(result.items[0]).toMatchObject({
      id: 'r-1',
      category: 'toxicity',
      enabled: true,
      default_action: 'flag',
      threshold: 0.8,
      updated_by: 'alice',
    });
    expect(result.hasNext).toBe(true);
    expect(result.total).toBe(50);
  });

  it('creates, updates and deletes AI rules with payload normalization', async () => {
    vi.mocked(apiPost).mockResolvedValue({
      id: 'r-2',
      category: 'spam',
      enabled: false,
      default_action: null,
      threshold: null,
    });

    const created = await createModerationAIRule({
      category: ' spam ',
      description: '  Detect spam ',
      defaultAction: '',
      threshold: null,
      enabled: false,
    });

    expect(apiPost).toHaveBeenCalledWith(
      '/api/moderation/ai-rules',
      { category: 'spam', description: 'Detect spam', default_action: null, threshold: null, enabled: false },
      { signal: undefined },
    );
    expect(created).toMatchObject({ id: 'r-2', category: 'spam', enabled: false });

    vi.mocked(apiPatch).mockResolvedValue({ id: 'r-2', category: 'spam', enabled: true, default_action: 'flag' });

    const updated = await updateModerationAIRule(' r-2 ', {
      description: null,
      defaultAction: 'flag',
      enabled: true,
    });

    expect(apiPatch).toHaveBeenCalledWith(
      '/api/moderation/ai-rules/r-2',
      { description: null, default_action: 'flag', enabled: true },
      { signal: undefined },
    );
    expect(updated).toMatchObject({ id: 'r-2', enabled: true, default_action: 'flag' });

    await deleteModerationAIRule(' r-2 ');
    expect(apiDelete).toHaveBeenCalledWith('/api/moderation/ai-rules/r-2', { signal: undefined });
  });
});
