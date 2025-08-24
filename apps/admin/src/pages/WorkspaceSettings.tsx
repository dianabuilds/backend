import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../api/client";
import { useToast } from "../components/ToastProvider";
import type {
  GenerateQuestIn,
  WorkspaceMemberOut,
  WorkspaceOut,
  WorkspaceRole,
} from "../openapi";
import PageLayout from "./_shared/PageLayout";

const TABS = [
  "General",
  "Members",
  "AI",
  "Notifications",
  "Limits",
] as const;

export default function WorkspaceSettings() {
  const { id } = useParams<{ id: string }>();
  const [tab, setTab] = useState<string>(TABS[0]);
  const { addToast } = useToast();

  const { data, isLoading, error } = useQuery({
    queryKey: ["workspace", id],
    enabled: !!id,
    queryFn: async () => {
      const res = await api.get<WorkspaceOut>(`/admin/workspaces/${id}`);
      return res.data as WorkspaceOut;
    },
  });

  useEffect(() => {
    if (error) {
      addToast({
        title: "Failed to load workspace",
        description: String(error),
        variant: "error",
      });
    }
  }, [error, addToast]);

  const [selectedPreset, setSelectedPreset] = useState("");
  const [aiForm, setAIForm] = useState<GenerateQuestIn>({
    structure: "",
    length: "",
    tone: "",
    genre: "",
    locale: "",
  });

  useEffect(() => {
    const keys = Object.keys(data?.settings?.ai_presets ?? {});
    if (keys.length > 0 && !selectedPreset) {
      setSelectedPreset(keys[0]);
    }
  }, [data, selectedPreset]);

  useEffect(() => {
    const preset = data?.settings?.ai_presets?.[selectedPreset] as
      | Partial<GenerateQuestIn>
      | undefined;
    if (preset) {
      setAIForm({
        structure: preset.structure ?? "",
        length: preset.length ?? "",
        tone: preset.tone ?? "",
        genre: preset.genre ?? "",
        locale: preset.locale ?? "",
        extras: preset.extras ?? undefined,
        world_template_id: preset.world_template_id ?? undefined,
      });
    }
  }, [data, selectedPreset]);

  const generateAI = async () => {
    try {
      await api.post(`/admin/ai/quests/generate`, aiForm);
      addToast({ title: "Generation enqueued", variant: "success" });
    } catch (e) {
      addToast({
        title: "Generation failed",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  const {
    data: members,
    isLoading: membersLoading,
    refetch: refetchMembers,
  } = useQuery({
    queryKey: ["workspace-members", id],
    enabled: tab === "Members" && !!id,
    queryFn: async () => {
      const res = await api.get<WorkspaceMemberOut[]>(
        `/admin/workspaces/${id}/members`,
      );
      return (res.data as WorkspaceMemberOut[]) || [];
    },
  });

  // Invite member modal
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteUser, setInviteUser] = useState("");
  const [inviteRole, setInviteRole] = useState<WorkspaceRole>("viewer");

  const inviteMember = async () => {
    try {
      await api.post(`/admin/workspaces/${id}/members`, {
        user_id: inviteUser,
        role: inviteRole,
      });
      addToast({ title: "Member invited", variant: "success" });
      setInviteOpen(false);
      setInviteUser("");
      setInviteRole("viewer");
      refetchMembers();
    } catch (e) {
      addToast({
        title: "Failed to invite member",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  // Change role modal
  const [editMember, setEditMember] = useState<WorkspaceMemberOut | null>(null);
  const [editRole, setEditRole] = useState<WorkspaceRole>("viewer");
  const openEdit = (m: WorkspaceMemberOut) => {
    setEditMember(m);
    setEditRole(m.role);
  };
  const applyEdit = async () => {
    if (!editMember) return;
    try {
      await api.patch(`/admin/workspaces/${id}/members/${editMember.user_id}`, {
        user_id: editMember.user_id,
        role: editRole,
      });
      addToast({ title: "Role updated", variant: "success" });
      setEditMember(null);
      refetchMembers();
    } catch (e) {
      addToast({
        title: "Failed to update role",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  // Remove modal
  const [removeMember, setRemoveMember] = useState<WorkspaceMemberOut | null>(
    null,
  );
  const confirmRemove = async () => {
    if (!removeMember) return;
    try {
      await api.del(`/admin/workspaces/${id}/members/${removeMember.user_id}`);
      addToast({ title: "Member removed", variant: "success" });
      setRemoveMember(null);
      refetchMembers();
    } catch (e) {
      addToast({
        title: "Failed to remove member",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  const renderMembers = () => (
    <div className="space-y-4">
      <button
        className="px-2 py-1 border rounded"
        onClick={() => setInviteOpen(true)}
      >
        Invite member
      </button>
      {membersLoading && <div>Loading...</div>}
      {!membersLoading && (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">User ID</th>
              <th className="p-2 text-left">Role</th>
              <th className="p-2" />
            </tr>
          </thead>
          <tbody>
            {members?.map((m) => (
              <tr key={m.user_id} className="border-b hover:bg-gray-50">
                <td className="p-2 font-mono">{m.user_id}</td>
                <td className="p-2 capitalize">{m.role}</td>
                <td className="p-2 space-x-2">
                  <button
                    className="text-blue-600 text-xs"
                    onClick={() => openEdit(m)}
                  >
                    Change role
                  </button>
                  <button
                    className="text-red-600 text-xs"
                    onClick={() => setRemoveMember(m)}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {inviteOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
          <div className="bg-white dark:bg-gray-900 rounded p-4 w-80 space-y-3">
            <h3 className="font-semibold">Invite member</h3>
            <input
              className="border rounded px-2 py-1 w-full"
              placeholder="User ID"
              value={inviteUser}
              onChange={(e) => setInviteUser(e.target.value)}
            />
            <select
              className="border rounded px-2 py-1 w-full"
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value as WorkspaceRole)}
            >
              <option value="owner">owner</option>
              <option value="editor">editor</option>
              <option value="viewer">viewer</option>
            </select>
            <div className="flex justify-end gap-2 pt-2">
              <button
                className="px-2 py-1"
                onClick={() => setInviteOpen(false)}
              >
                Cancel
              </button>
              <button
                className="px-2 py-1 border rounded"
                onClick={inviteMember}
              >
                Invite
              </button>
            </div>
          </div>
        </div>
      )}

      {editMember && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
          <div className="bg-white dark:bg-gray-900 rounded p-4 w-80 space-y-3">
            <h3 className="font-semibold">Change role</h3>
            <select
              className="border rounded px-2 py-1 w-full"
              value={editRole}
              onChange={(e) => setEditRole(e.target.value as WorkspaceRole)}
            >
              <option value="owner">owner</option>
              <option value="editor">editor</option>
              <option value="viewer">viewer</option>
            </select>
            <div className="flex justify-end gap-2 pt-2">
              <button className="px-2 py-1" onClick={() => setEditMember(null)}>
                Cancel
              </button>
              <button className="px-2 py-1 border rounded" onClick={applyEdit}>
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {removeMember && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
          <div className="bg-white dark:bg-gray-900 rounded p-4 w-80 space-y-3">
            <h3 className="font-semibold">Remove member</h3>
            <p className="text-sm">Remove {removeMember.user_id}?</p>
            <div className="flex justify-end gap-2 pt-2">
              <button
                className="px-2 py-1"
                onClick={() => setRemoveMember(null)}
              >
                Cancel
              </button>
              <button
                className="px-2 py-1 border rounded text-red-600"
                onClick={confirmRemove}
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderAI = () => {
    const presets = data?.settings?.ai_presets ?? {};
    const presetKeys = Object.keys(presets);

    if (presetKeys.length === 0) {
      return (
        <div className="text-sm text-gray-500">No AI presets configured.</div>
      );
    }

    return (
      <div className="space-y-2 text-sm">
        <select
          className="border rounded px-2 py-1"
          value={selectedPreset}
          onChange={(e) => setSelectedPreset(e.target.value)}
        >
          {presetKeys.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <input
          className="border rounded px-2 py-1 w-full"
          placeholder="Structure"
          value={aiForm.structure}
          onChange={(e) => setAIForm({ ...aiForm, structure: e.target.value })}
        />
        <input
          className="border rounded px-2 py-1 w-full"
          placeholder="Length"
          value={aiForm.length}
          onChange={(e) => setAIForm({ ...aiForm, length: e.target.value })}
        />
        <input
          className="border rounded px-2 py-1 w-full"
          placeholder="Tone"
          value={aiForm.tone}
          onChange={(e) => setAIForm({ ...aiForm, tone: e.target.value })}
        />
        <input
          className="border rounded px-2 py-1 w-full"
          placeholder="Genre"
          value={aiForm.genre}
          onChange={(e) => setAIForm({ ...aiForm, genre: e.target.value })}
        />
        <input
          className="border rounded px-2 py-1 w-full"
          placeholder="Locale"
          value={aiForm.locale ?? ""}
          onChange={(e) => setAIForm({ ...aiForm, locale: e.target.value })}
        />
        <button className="px-2 py-1 border rounded" onClick={generateAI}>
          Generate
        </button>
      </div>
    );
  };

  const renderTab = () => {
    switch (tab) {
      case "General":
        return data ? (
          <div className="text-sm space-y-1">
            <div>
              <b>ID:</b> {data.id}
            </div>
            <div>
              <b>Name:</b> {data.name}
            </div>
            <div>
              <b>Slug:</b> {data.slug}
            </div>
          </div>
        ) : null;
      case "Members":
        return renderMembers();
      case "AI":
        return renderAI();
      default:
        return (
          <div className="text-sm text-gray-500">No content for {tab} yet.</div>
        );
    }
  };

  if (!id) {
    return (
      <PageLayout title="Workspace settings">
        <div>Select workspace</div>
      </PageLayout>
    );
  }

  return (
    <PageLayout title="Workspace settings">
      <div className="border-b flex gap-4 mt-4">
        {TABS.map((t) => (
          <button
            key={t}
            className={`py-2 text-sm ${tab === t ? "border-b-2 border-blue-500 text-blue-600" : "text-gray-600"}`}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>
      <div className="mt-4">
        {isLoading ? <div>Loading...</div> : renderTab()}
      </div>
    </PageLayout>
  );
}
