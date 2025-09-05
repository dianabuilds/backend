import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { Workspace } from "../api/types";
import { useToast } from "../components/ToastProvider";
import { useWorkspace } from "../workspace/WorkspaceContext";
import PageLayout from "./_shared/PageLayout";

type MeResponse = {
  username: string | null;
  bio: string | null;
  avatar_url: string | null;
  default_workspace_id: string | null;
};

const isValidUrl = (s: string): boolean => {
  try {
    new URL(s);
    return true;
  } catch {
    return false;
  }
};

export default function Profile() {
  const { addToast } = useToast();
  const { setWorkspace } = useWorkspace();
  const [defaultWs, setDefaultWs] = useState<string>("");
  const [username, setUsername] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");

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
    queryFn: async () => (await api.get<MeResponse>("/users/me")).data,
  });

  useEffect(() => {
    if (me) {
      setDefaultWs(me.default_workspace_id ?? "");
      setUsername(me.username ?? "");
      setBio(me.bio ?? "");
      setAvatarUrl(me.avatar_url ?? "");
    }
  }, [me]);

  const saveProfile = async () => {
    const u = username.trim();
    const b = bio.trim();
    const a = avatarUrl.trim();
    if (!u) {
      addToast({ title: "Username is required", variant: "error" });
      return;
    }
    if (a && !isValidUrl(a)) {
      addToast({ title: "Invalid avatar URL", variant: "error" });
      return;
    }
    try {
      await api.patch("/users/me", {
        username: u,
        bio: b || null,
        avatar_url: a || null,
      });
      addToast({ title: "Profile saved", variant: "success" });
    } catch (e) {
      addToast({
        title: "Save failed",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

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
        <label className="text-sm" htmlFor="username">
          Username
        </label>
        <input
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="px-2 py-1 border rounded text-sm"
        />
        <label className="text-sm" htmlFor="bio">
          Bio
        </label>
        <textarea
          id="bio"
          value={bio}
          onChange={(e) => setBio(e.target.value)}
          className="px-2 py-1 border rounded text-sm"
        />
        <label className="text-sm" htmlFor="avatar-url">
          Avatar URL
        </label>
        <input
          id="avatar-url"
          value={avatarUrl}
          onChange={(e) => setAvatarUrl(e.target.value)}
          className="px-2 py-1 border rounded text-sm"
        />
        <button
          onClick={saveProfile}
          className="mt-2 self-start px-3 py-1 rounded bg-gray-800 text-white text-sm"
        >
          Save profile
        </button>
      </div>
      <div className="max-w-sm flex flex-col gap-2 mt-8">
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
