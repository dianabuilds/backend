/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { nodesApi } from "../api/nodes.api";
import type { NodeEditorData } from "../model/node";

export function useNodeEditor(
  workspaceId: string | undefined,
  id: number | "new",
) {
  const queryClient = useQueryClient();
  const isNew = id === "new";

  const { data, isLoading, error } = useQuery({
    queryKey: ["node", workspaceId ?? "global", id],
    queryFn: () => nodesApi.get(workspaceId, id as number),
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
        coverUrl: (data as any).coverUrl ?? (data as any).cover_url ?? null,
        media: ((data as any).media as string[] | undefined) ?? [],
        tags:
          ((data as any).tagSlugs as string[] | undefined) ??
          ((data as any).tag_slugs as string[] | undefined) ??
          ((data as any).tags as string[] | undefined) ??
          [],
        isPublic: (data as any).isPublic ?? (data as any).is_public ?? false,
        content,
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
      };
      if (payload.tags) body.tagSlugs = payload.tags;
      if (isNew) {
        return nodesApi.create(workspaceId, body as any);
      }
      return nodesApi.update(workspaceId, payload.id as number, body as any);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["node", workspaceId ?? "global", id],
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
