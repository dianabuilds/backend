import { useQuery } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";
import { useParams } from "react-router-dom";

import { api } from "../api/client";
import {
  getAIPresets,
  saveAIPresets,
  validateAIPresets,
  getNotificationRules,
  saveNotificationRules,
  validateNotificationRules,
  getLimits,
  saveLimits,
  validateLimits,
} from "../api/workspaceSettings";
import { useToast } from "../components/ToastProvider";
import type { WorkspaceMemberOut, WorkspaceOut, WorkspaceRole } from "../openapi";
import PageLayout from "./_shared/PageLayout";

const TABS = [
  "General",
  "Members",
  "AI-presets",
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

  const [aiPresetsText, setAIPresetsText] = useState("{}");
  const [notificationsText, setNotificationsText] = useState("{}");
  const [limitsText, setLimitsText] = useState("{}");
  const [aiError, setAiError] = useState<string | null>(null);
  const [notificationsError, setNotificationsError] = useState<string | null>(
    null,
  );
  const [limitsError, setLimitsError] = useState<string | null>(null);

  const {
    data: aiPresetsData,
    isLoading: aiPresetsLoading,
    refetch: refetchAIPresets,
  } = useQuery({
    queryKey: ["workspace-ai-presets", id],
    enabled: tab === "AI-presets" && !!id,
    queryFn: async () => getAIPresets(id!),
  });

  const {
    data: notificationsData,
    isLoading: notificationsLoading,
    refetch: refetchNotifications,
  } = useQuery({
    queryKey: ["workspace-notifications", id],
    enabled: tab === "Notifications" && !!id,
    queryFn: async () => getNotificationRules(id!),
  });

  const {
    data: limitsData,
    isLoading: limitsLoading,
    refetch: refetchLimits,
  } = useQuery({
    queryKey: ["workspace-limits", id],
    enabled: tab === "Limits" && !!id,
    queryFn: async () => getLimits(id!),
  });

  useEffect(() => {
    if (aiPresetsData) {
      setAIPresetsText(JSON.stringify(aiPresetsData, null, 2));
    }
  }, [aiPresetsData]);

  useEffect(() => {
    if (notificationsData) {
      setNotificationsText(JSON.stringify(notificationsData, null, 2));
    }
  }, [notificationsData]);

  useEffect(() => {
    if (limitsData) {
      setLimitsText(JSON.stringify(limitsData, null, 2));
    }
  }, [limitsData]);

  const savePresets = async (e: FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      setAiError(null);
      const parsed = aiPresetsText ? JSON.parse(aiPresetsText) : {};
      await validateAIPresets(id, parsed);
      await saveAIPresets(id, parsed);
      addToast({ title: "Presets saved", variant: "success" });
      await refetchAIPresets();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setAiError(msg);
    }
  };

  const saveNotificationsSettings = async (e: FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      setNotificationsError(null);
      const parsed = notificationsText ? JSON.parse(notificationsText) : {};
      await validateNotificationRules(id, parsed);
      await saveNotificationRules(id, parsed);
      addToast({ title: "Notifications saved", variant: "success" });
      await refetchNotifications();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setNotificationsError(msg);
    }
  };

  const saveLimitsSettings = async (e: FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      setLimitsError(null);
      const parsed = limitsText ? JSON.parse(limitsText) : {};
      await validateLimits(id, parsed);
      await saveLimits(id, parsed);
      addToast({ title: "Limits saved", variant: "success" });
      await refetchLimits();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setLimitsError(msg);
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

  const renderAIPresets = () => (
    <div className="space-y-2">
      {aiPresetsLoading ? (
        <div>Loading...</div>
      ) : (
        <form onSubmit={savePresets} className="space-y-2">
          <textarea
            className="border rounded w-full h-64 p-2 font-mono text-xs"
            value={aiPresetsText}
            onChange={(e) => setAIPresetsText(e.target.value)}
          />
          {aiError && (
            <div className="text-sm text-red-600 whitespace-pre-wrap">
              {aiError}
            </div>
          )}
          <button type="submit" className="px-2 py-1 border rounded">
            Save
          </button>
        </form>
      )}
    </div>
  );

  const renderNotifications = () => (
    <div className="space-y-2">
      {notificationsLoading ? (
        <div>Loading...</div>
      ) : (
        <form onSubmit={saveNotificationsSettings} className="space-y-2">
          <textarea
            className="border rounded w-full h-64 p-2 font-mono text-xs"
            value={notificationsText}
            onChange={(e) => setNotificationsText(e.target.value)}
          />
          {notificationsError && (
            <div className="text-sm text-red-600 whitespace-pre-wrap">
              {notificationsError}
            </div>
          )}
          <button type="submit" className="px-2 py-1 border rounded">
            Save
          </button>
        </form>
      )}
    </div>
  );

  const renderLimits = () => (
    <div className="space-y-2">
      {limitsLoading ? (
        <div>Loading...</div>
      ) : (
        <form onSubmit={saveLimitsSettings} className="space-y-2">
          <textarea
            className="border rounded w-full h-64 p-2 font-mono text-xs"
            value={limitsText}
            onChange={(e) => setLimitsText(e.target.value)}
          />
          {limitsError && (
            <div className="text-sm text-red-600 whitespace-pre-wrap">
              {limitsError}
            </div>
          )}
          <button type="submit" className="px-2 py-1 border rounded">
            Save
          </button>
        </form>
      )}
    </div>
  );

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
      case "AI-presets":
        return renderAIPresets();
      case "Notifications":
        return renderNotifications();
      case "Limits":
        return renderLimits();
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
