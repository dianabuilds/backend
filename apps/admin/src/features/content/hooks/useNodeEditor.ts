/* eslint-disable @typescript-eslint/no-explicit-any */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { nodesApi } from "../api/nodes.api";
import type { NodeEditorData } from "../model/node";

export function useNodeEditor(workspaceId: string, id: string) {
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
  });

  useEffect(() => {
    if (data) {
      setNode({
        id: String(data.id),
        title: data.title ?? "",
        slug: (data as any).slug ?? "",
      });
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: async (payload: NodeEditorData) => {
      const body: any = {
        title: payload.title,
        slug: payload.slug,
      };
      if (isNew) {
        return nodesApi.create(workspaceId, body as any);
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
