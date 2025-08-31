/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { nodesApi } from "../api/nodes.api";
import type { NodeEditorData } from "../model/node";

export function useNodeEditor(workspaceId: string, nodeType: string, id: string) {
  const queryClient = useQueryClient();
  const isNew = id === "new";

  const { data, isLoading, error } = useQuery({
    queryKey: ["node", workspaceId, id],
    queryFn: () => nodesApi.get(workspaceId, id),
    enabled: !isNew,
  });

  const [node, setNode] = useState<NodeEditorData>({
    id: id === "new" ? undefined : id,
    title: "",
    slug: "",
    content: { blocks: [] },
    coverUrl: null,
    tags: [],
    isPublic: false,
    premiumOnly: false,
    allowComments: true,
  });

  useEffect(() => {
    if (data) {
      setNode({
        id: String(data.id),
        title: data.title ?? "",
        slug: (data as any).slug ?? "",
        content: (data as any).content ?? { blocks: [] },
        coverUrl: (data as any).coverUrl ?? (data as any).cover_url ?? null,
        tags: (data as any).tags ?? [],
        isPublic: Boolean((data as any).isPublic ?? (data as any).is_public),
        premiumOnly: Boolean((data as any).premiumOnly ?? (data as any).premium_only),
        allowComments: Boolean(
          (data as any).allowFeedback ??
            (data as any).allow_comments ??
            (data as any).allowComments ??
            true,
        ),
      });
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: async (payload: NodeEditorData) => {
      const body: any = {
        title: payload.title,
        slug: payload.slug,
        content: payload.content as any,
        is_public: payload.isPublic,
        tags: payload.tags,
        cover_url: payload.coverUrl,
        premium_only: payload.premiumOnly,
        allow_comments: payload.allowComments,
      };
      if (isNew) {
        return nodesApi.create(workspaceId, {
          node_type: nodeType,
          ...body,
        } as any);
      }
      return nodesApi.update(workspaceId, payload.id as string, body as any);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["node", workspaceId, id] });
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
