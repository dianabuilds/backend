/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { nodesApi } from "../api/nodes.api";
import type { NodeEditorData } from "../model/node";

export function normalizeTags(src: unknown): string[] {
  // Пытаемся найти массив тегов в разных местах ответа
  const top: any = (src as any)?.tags;
  const meta: any = (src as any)?.meta?.tags;
  const input: any = Array.isArray(top) ? top : Array.isArray(meta) ? meta : src;

  if (!Array.isArray(input)) return [];
  return (input as any[])
    .map((t) => {
      if (typeof t === "string") return t;
      if (t && typeof t === "object") {
        // поддерживаем как объекты тегов { slug, name }, так и простые строки
        return (t as any).slug ?? (t as any).name ?? null;
      }
      return null;
    })
    .filter((t): t is string => typeof t === "string" && t.length > 0);
}

export function useNodeEditor(
  accountId: string,
  id: number | "new",
) {
  const queryClient = useQueryClient();
  const isNew = id === "new";

  const { data, isLoading, error } = useQuery({
    queryKey: ["node", accountId || "personal", id],
    queryFn: () => nodesApi.get(accountId, id as number),
    enabled: !isNew,
  });

  const [node, setNode] = useState<NodeEditorData>({
    id: id === "new" ? undefined : (id as number),
    title: "",
    slug: "",
    coverUrl: null,
    media: [],
    tags: [],
    isPublic: false,
    content: { time: Date.now(), blocks: [], version: "2.30.7" },
    context: "default",
    space: "",
    roles: [],
    override: false,
  });

  useEffect(() => {
    if (data) {
      let content: any = (data as any).content;
      if (typeof content === "string") {
        try {
          content = JSON.parse(content);
        } catch {
          content = { time: Date.now(), blocks: [], version: "2.30.7" };
        }
      }
      if (!content || typeof content !== "object") {
        content = { time: Date.now(), blocks: [], version: "2.30.7" };
      }
      setNode({
        id: (data as any).id,
        title: (data as any).title ?? "",
        slug: (data as any).slug ?? "",
        coverUrl: (data as any).coverUrl ?? null,
        media: ((data as any).media as string[] | undefined) ?? [],
        tags: normalizeTags(data),
        isPublic: (data as any).isPublic ?? (data as any).is_public ?? false,
        content,
        context: (data as any).context ?? "default",
        space: (data as any).space ?? "",
        roles: ((data as any).roles as string[] | undefined) ?? [],
        override: (data as any).override ?? false,
      });
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: async (payload: NodeEditorData) => {
      const body: any = {
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
        return nodesApi.create(accountId, body as any);
      }
      return nodesApi.update(accountId, payload.id as number, body as any);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["node", accountId || "global", id],
      });
    },
  });

  const update = (patch: Partial<NodeEditorData>) =>
    setNode((prev) => ({ ...prev, ...patch }));

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

export default useNodeEditor;
