import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import PageLayout from "./_shared/PageLayout";
import { api } from "../api/client";
import { useToast } from "../components/ToastProvider";
import { useWorkspace } from "../workspace/WorkspaceContext";
import type { Workspace } from "../api/types";

export default function Profile() {
  const { addToast } = useToast();
  const { setWorkspace } = useWorkspace();
  const [defaultWs, setDefaultWs] = useState<string>(
    () => (typeof localStorage !== "undefined" && localStorage.getItem("defaultWorkspaceId")) || ""
  );

  const { data } = useQuery({
    queryKey: ["workspaces"],
    queryFn: async () => {
      const res = await api.get<Workspace[] | { workspaces: Workspace[] }>("/admin/workspaces");
      const payload = res.data;
      if (Array.isArray(payload)) return payload;
      return payload?.workspaces ?? [];
    },
  });

  const save = () => {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("defaultWorkspaceId", defaultWs);
    }
    setWorkspace(data?.find((ws) => ws.id === defaultWs));
    addToast({ title: "Default workspace saved", variant: "success" });
  };

  return (
    <PageLayout title="Profile">
      <div className="max-w-sm flex flex-col gap-2">
        <label className="text-sm" htmlFor="def-ws">Default workspace</label>
        <select
          id="def-ws"
          value={defaultWs}
          onChange={(e) => setDefaultWs(e.target.value)}
          className="px-2 py-1 border rounded text-sm"
        >
          <option value="">None</option>
          {data?.map((ws) => (
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
