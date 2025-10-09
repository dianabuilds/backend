import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./client', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}));

import { apiDelete, apiGet, apiPost } from './client';
import {
  bulkUpdateNodesStatus,
  deleteNode,
  fetchNodeAuthor,
  fetchNodesList,
  restoreNode,
  searchNodeAuthors,
} from './nodes';

const mockedApiGet = vi.mocked(apiGet);
const mockedApiPost = vi.mocked(apiPost);
const mockedApiDelete = vi.mocked(apiDelete);

describe('nodes api', () => {
  beforeEach(() => {
    mockedApiGet.mockReset();
    mockedApiPost.mockReset();
    mockedApiDelete.mockReset();
  });

  describe('fetchNodesList', () => {
    it('normalizes list responses with metadata and filters params', async () => {
      mockedApiGet.mockResolvedValue({
        data: {
          items: [
            {
              id: 7,
              title: 'First node',
              slug: '',
              author_id: 'user-1',
              author_name: null,
              embedding_status: 'ready',
              status: 'draft',
              updated_at: '2025-10-05T12:00:00Z',
            },
            {
              id: 'node-2',
              title: null,
              embedding_ready: false,
              embedding: [1, 2],
              is_public: true,
              status: 'published',
              updated_at: null,
            },
          ],
          total: '10',
          has_next: 'true',
          stats: {
            published_count: '3',
            draft_total: 7,
            pending_embeddings: '2',
          },
        },
      });

      const result = await fetchNodesList({
        q: ' test ',
        slug: ' sluggy ',
        status: 'draft',
        authorId: ' author-1 ',
        sort: 'status',
        order: 'asc',
        limit: 15,
        offset: 30,
      });

      expect(mockedApiGet).toHaveBeenCalledWith(
        '/v1/admin/nodes/list?q=test&slug=sluggy&limit=15&offset=30&sort=status&order=asc&status=draft&author_id=author-1',
        { signal: undefined },
      );

      expect(result.items).toEqual([
        {
          id: '7',
          title: 'First node',
          slug: 'node-7',
          author_id: 'user-1',
          author_name: null,
          is_public: undefined,
          status: 'draft',
          updated_at: '2025-10-05T12:00:00Z',
          embedding_status: 'ready',
          embedding_ready: true,
        },
        {
          id: 'node-2',
          title: undefined,
          slug: 'node-node-2',
          author_id: null,
          author_name: null,
          is_public: true,
          status: 'published',
          updated_at: null,
          embedding_status: 'ready',
          embedding_ready: true,
        },
      ]);
      expect(result.meta).toEqual({ total: 10, published: 3, drafts: 7, pendingEmbeddings: 2 });
      expect(result.hasNext).toBe(true);
    });

    it('handles array responses and omits default filters', async () => {
      mockedApiGet.mockResolvedValue([
        { id: 1, title: 'A' },
        { id: 2, title: 'B' },
      ]);

      const result = await fetchNodesList({ status: 'all' });

      expect(mockedApiGet).toHaveBeenCalledWith('/v1/admin/nodes/list?limit=20&offset=0', { signal: undefined });
      expect(result.items).toHaveLength(2);
      expect(result.meta).toEqual({ total: 2, published: null, drafts: null, pendingEmbeddings: null });
      expect(result.hasNext).toBe(false);
    });
  });

  describe('nodes mutations', () => {
    it('restores node with trimmed id', async () => {
      mockedApiPost.mockResolvedValue(undefined);
      await restoreNode('  node-42  ');
      expect(mockedApiPost).toHaveBeenCalledWith('/v1/admin/nodes/node-42/restore', {}, { signal: undefined });
    });

    it('deletes node with trimmed id', async () => {
      mockedApiDelete.mockResolvedValue(undefined);
      await deleteNode(' node-13 ');
      expect(mockedApiDelete).toHaveBeenCalledWith('/v1/admin/nodes/node-13', { signal: undefined });
    });

    it('bulk updates node statuses and deduplicates ids', async () => {
      mockedApiPost.mockResolvedValue(undefined);
      await bulkUpdateNodesStatus({
        ids: [' a ', 'b', 'a', ''],
        status: 'archived',
        publish_at: ' 2025-10-01T10:00 ',
      });
      expect(mockedApiPost).toHaveBeenCalledWith(
        '/v1/admin/nodes/bulk/status',
        { ids: ['a', 'b'], status: 'archived', publish_at: '2025-10-01T10:00' },
        { signal: undefined },
      );
    });

    it('throws when bulk update receives no ids', async () => {
      await expect(bulkUpdateNodesStatus({ ids: [], status: 'draft' })).rejects.toThrow('nodes_bulk_ids_missing');
    });
  });

  describe('nodes authors api', () => {
    it('returns empty array for blank query', async () => {
      const result = await searchNodeAuthors('   ');
      expect(result).toEqual([]);
      expect(mockedApiGet).not.toHaveBeenCalled();
    });

    it('searches authors and normalizes options', async () => {
      mockedApiGet.mockResolvedValue([
        { id: 'user-1', username: 'alpha' },
        { id: 2, username: '  ' },
        'invalid',
      ]);

      const result = await searchNodeAuthors(' Query ', { limit: 5 });

      expect(mockedApiGet).toHaveBeenCalledWith('/v1/users/search?q=Query&limit=5', { signal: undefined });
      expect(result).toEqual([
        { id: 'user-1', username: 'alpha' },
        { id: '2', username: '2' },
      ]);
    });

    it('fetches single author and falls back to id when username missing', async () => {
      mockedApiGet.mockResolvedValue({ id: 99, email: 'user@example.com' });
      const result = await fetchNodeAuthor(' 99 ');
      expect(mockedApiGet).toHaveBeenCalledWith('/v1/users/99', { signal: undefined });
      expect(result).toEqual({ id: '99', username: '99' });
    });
  });
});

