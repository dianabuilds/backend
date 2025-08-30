import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
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
    content: "",
    isPublic: false,
  });

  useEffect(() => {
    if (data) {
      setNode({
        id: String(data.id),
        title: data.title ?? "",
        slug: (data as any).slug ?? "",
        content: JSON.stringify((data as any).content ?? ""),
        isPublic: Boolean((data as any).isPublic ?? (data as any).is_public),
      });
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: async (payload: NodeEditorData) => {
      if (isNew) {
        return nodesApi.create(workspaceId, {
          node_type: nodeType,
          title: payload.title,
          slug: payload.slug,
          content: payload.content as any,
          is_public: payload.isPublic,
        } as any);
      }
      return nodesApi.update(workspaceId, payload.id as string, {
        title: payload.title,
        slug: payload.slug,
        content: payload.content as any,
        is_public: payload.isPublic,
      } as any);
    },
    onSuccess: (res) => {
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
