import { useQuery } from "@tanstack/react-query";
import { ArrowRightLeft, Settings } from "lucide-react";
import { useCallback, useEffect } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import type { Workspace } from "../api/types";
import { useWorkspace } from "../workspace/WorkspaceContext";
import SelectBase from "./ui/SelectBase";

export default function WorkspaceSelector() {
  const { workspaceId, setWorkspace } = useWorkspace();

  const { data } = useQuery({
    queryKey: ["workspaces"],
    queryFn: async () => {
      const res = await api.get<Workspace[] | { workspaces: Workspace[] }>(
        "/admin/workspaces",
      );
      const payload = res.data;
      if (Array.isArray(payload)) return payload;
      return payload?.workspaces ?? [];
    },
  });

  useEffect(() => {
    if (!workspaceId && data && data.length > 0) {
      setWorkspace(data[0]);
    }
  }, [workspaceId, data, setWorkspace]);

  const selected = data?.find((ws) => ws.id === workspaceId);

  const quickSwitch = useCallback(() => {
    if (!data || data.length === 0) return;
    const idx = data.findIndex((ws) => ws.id === workspaceId);
    const next = data[(idx + 1) % data.length];
    setWorkspace(next);
  }, [data, workspaceId, setWorkspace]);

  return (
    <div className="flex items-center gap-2 mr-4">
      <SelectBase<Workspace>
        items={data ?? []}
        value={selected}
        onChange={setWorkspace}
        getKey={(ws) => ws.id}
        getLabel={(ws) => ws.name}
      />
      <button
        onClick={quickSwitch}
        title="Quick switch workspace"
        className="text-gray-600 hover:text-gray-900"
        type="button"
      >
        <ArrowRightLeft className="w-4 h-4" />
      </button>
      {workspaceId && selected && (
        <Link
          to={`/workspaces/${workspaceId}`}
          className="text-gray-600 hover:text-gray-900"
          title={`Settings for ${selected.name}`}
        >
          <Settings className="w-4 h-4" />
        </Link>
      )}
    </div>
  );
}
