import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import type { NodeMutationPayload } from '../api/nodes.api';
import { nodesApi } from '../api/nodes.api';
import type { NodeEditorData } from '../model/node';

export function normalizeTags(src: unknown): string[] {
  // Пытаемся найти массив тегов в разных местах ответа
  const top = src && typeof src === 'object' ? (src as Record<string, unknown>).tags : undefined;
  const metaTags =
    src && typeof src === 'object'
      ? (src as Record<string, unknown>).meta &&
        (src as Record<string, unknown>).meta &&
        (src as Record<string, { tags?: unknown }>).meta?.tags
      : undefined;
  const input = Array.isArray(top) ? top : Array.isArray(metaTags) ? metaTags : src;

  if (!Array.isArray(input)) return [];
  return input
    .map((t) => {
      if (typeof t === 'string') return t;
      if (t && typeof t === 'object') {
        const o = t as Record<string, unknown>;
        const v = (o.slug ?? o.name) as unknown;
        return typeof v === 'string' ? v : null;
      }
      return null;
    })
    .filter((t): t is string => typeof t === 'string' && t.length > 0);
}

export function useNodeEditor(accountId: string, id: number | 'new') {
  const queryClient = useQueryClient();
  const isNew = id === 'new';

  const { data, isLoading, error } = useQuery({
    queryKey: ['node', accountId || 'personal', id],
    queryFn: () => nodesApi.get(accountId, id as number),
    enabled: !isNew,
  });

  const [node, setNode] = useState<NodeEditorData>({
    id: id === 'new' ? undefined : (id as number),
    title: '',
    slug: '',
    coverUrl: null,
    media: [],
    tags: [],
    isPublic: false,
    content: { time: Date.now(), blocks: [], version: '2.30.7' },
    context: 'default',
    space: '',
    roles: [],
    override: false,
  });

  useEffect(() => {
    if (data) {
      let content: unknown = (data as unknown as { content?: unknown }).content;
      if (typeof content === 'string') {
        try {
          content = JSON.parse(content);
        } catch {
          content = { time: Date.now(), blocks: [], version: '2.30.7' };
        }
      }
      if (!content || typeof content !== 'object') {
        content = { time: Date.now(), blocks: [], version: '2.30.7' };
      }
      setNode({
        id: (data as { id?: number }).id,
        title: (data as { title?: string }).title ?? '',
        slug: (data as { slug?: string }).slug ?? '',
        coverUrl: (data as { coverUrl?: string | null }).coverUrl ?? null,
        media: ((data as { media?: string[] }).media as string[] | undefined) ?? [],
        tags: normalizeTags(data),
        isPublic:
          (data as { isPublic?: boolean; is_public?: boolean }).isPublic ??
          (data as { is_public?: boolean }).is_public ??
          false,
        content,
        context: (data as { context?: string }).context ?? 'default',
        space: (data as { space?: string }).space ?? '',
        roles: ((data as { roles?: string[] }).roles as string[] | undefined) ?? [],
        override: (data as { override?: boolean }).override ?? false,
      });
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: async (payload: NodeEditorData) => {
      const body: NodeMutationPayload = {
        title: payload.title,
        slug: payload.slug,
        coverUrl: payload.coverUrl,
        media: payload.media,
        content: payload.content, // EditorJS document
        context: payload.context,
        space: payload.space,
        roles: payload.roles,
        override: payload.override,
      };
      // ВАЖНО: отправляем tags всегда, если свойство определено, даже если [] — это позволяет очищать теги
      if (payload.tags !== undefined) body.tags = payload.tags;
      if (isNew) {
        return nodesApi.create(accountId, body);
      }
      return nodesApi.update(accountId, payload.id as number, body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['node', accountId || 'global', id],
      });
    },
  });

  const update = (patch: Partial<NodeEditorData>) => setNode((prev) => ({ ...prev, ...patch }));

  const save = () => mutation.mutateAsync(node);

  return {
    node,
    update,
    save,
    isSaving: mutation.isPending,
    loading: isLoading,
    error,
    isNew,
  };
}

// No default export to avoid duplicate exports; import as named: { useNodeEditor }
