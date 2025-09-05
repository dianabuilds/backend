import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { Workspace } from "../api/types";
import { useToast } from "../components/ToastProvider";
import { useWorkspace } from "../workspace/WorkspaceContext";
import PageLayout from "./_shared/PageLayout";

export default function Profile() {
  const { addToast } = useToast();
  const { setWorkspace } = useWorkspace();
  const [defaultWs, setDefaultWs] = useState<string>("");

  const { data: workspaces } = useQuery({
    queryKey: ["workspaces"],
    queryFn: async () => {
      const res = await api.get<Workspace[] | { workspaces: Workspace[] }>(
        "/workspaces",
      );
      const payload = res.data;
      if (Array.isArray(payload)) return payload;
      return payload?.workspaces ?? [];
    },
  });

  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: async () => (
      await api.get<{ default_workspace_id: string | null }>("/users/me")
    ).data,
  });

  useEffect(() => {
    if (me) setDefaultWs(me.default_workspace_id ?? "");
  }, [me]);

  const save = async () => {
    await api.patch("/users/me/default-workspace", {
      default_workspace_id: defaultWs || null,
    });
    setWorkspace(workspaces?.find((ws) => ws.id === defaultWs));
    addToast({ title: "Default workspace saved", variant: "success" });
  };

  return (
    <PageLayout title="Profile">
      <div className="max-w-sm flex flex-col gap-2">
        <label className="text-sm" htmlFor="def-ws">
          Default workspace
        </label>
        <select
          id="def-ws"
          value={defaultWs}
          onChange={(e) => setDefaultWs(e.target.value)}
          className="px-2 py-1 border rounded text-sm"
        >
          <option value="">None</option>
          {workspaces?.map((ws) => (
            <option key={ws.id} value={ws.id}>
              {ws.name}
            </option>
          ))}
        </select>
        <button
          onClick={save}
          className="mt-2 self-start px-3 py-1 rounded bg-gray-800 text-white text-sm"
        >
          Save
        </button>
      </div>
    </PageLayout>
  );
}
