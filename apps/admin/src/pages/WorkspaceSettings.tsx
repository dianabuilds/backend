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
  type AIPresets,
  type NotificationRules,
  type WorkspaceLimits,
  type NotificationChannel,
} from "../api/workspaceSettings";
import { useToast } from "../components/ToastProvider";
import Tooltip from "../components/Tooltip";
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

  const { data: globalAi } = useQuery({
    queryKey: ["global-ai-settings"],
    queryFn: async () => {
      const res = await api.get<{ model?: string; provider?: string }>(
        "/admin/ai/settings",
      );
      return res.data ?? {};
    },
  });

  const { data: globalLimits } = useQuery({
    queryKey: ["global-premium-limits"],
    queryFn: async () => {
      const res = await api.get<WorkspaceLimits>("/admin/premium/limits");
      return (
        res.data ?? { ai_tokens: 0, notif_per_day: 0, compass_calls: 0 }
      );
    },
  });

  const [aiPresets, setAIPresets] = useState<AIPresets>({
    provider: "",
    forbidden: [],
  });
  const [notifications, setNotifications] = useState<NotificationRules>({
    achievement: [],
    publish: [],
  });
  const [limits, setLimitsState] = useState<WorkspaceLimits>({
    ai_tokens: 0,
    notif_per_day: 0,
    compass_calls: 0,
  });
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
      setAIPresets({
        provider: aiPresetsData.provider ?? "",
        model: aiPresetsData.model ?? "",
        temperature: aiPresetsData.temperature,
        system_prompt: aiPresetsData.system_prompt ?? "",
        forbidden: aiPresetsData.forbidden ?? [],
      });
    }
  }, [aiPresetsData]);

  useEffect(() => {
    if (notificationsData) {
      setNotifications({
        achievement: notificationsData.achievement ?? [],
        publish: notificationsData.publish ?? [],
      });
    }
  }, [notificationsData]);

  useEffect(() => {
    if (limitsData) {
      setLimitsState({
        ai_tokens: limitsData.ai_tokens ?? 0,
        notif_per_day: limitsData.notif_per_day ?? 0,
        compass_calls: limitsData.compass_calls ?? 0,
      });
    }
  }, [limitsData]);

  const effectiveProvider = aiPresets.provider || globalAi?.provider || "";
  const providerSource = aiPresets.provider
    ? "workspace"
    : globalAi?.provider
    ? "global"
    : "";
  const effectiveModel = aiPresets.model || globalAi?.model || "";
  const modelSource = aiPresets.model
    ? "workspace"
    : globalAi?.model
    ? "global"
    : "";
  const effectiveLimits = {
    ai_tokens: limits.ai_tokens || globalLimits?.ai_tokens || 0,
    notif_per_day: limits.notif_per_day || globalLimits?.notif_per_day || 0,
    compass_calls: limits.compass_calls || globalLimits?.compass_calls || 0,
  };
  const limitSource = {
    ai_tokens: limits.ai_tokens ? "workspace" : "global",
    notif_per_day: limits.notif_per_day ? "workspace" : "global",
    compass_calls: limits.compass_calls ? "workspace" : "global",
  };

  const savePresets = async (e: FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      setAiError(null);
      await validateAIPresets(id, aiPresets);
      await saveAIPresets(id, aiPresets);
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
      await validateNotificationRules(id, notifications);
      await saveNotificationRules(id, notifications);
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
      await validateLimits(id, limits);
      await saveLimits(id, limits);
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
    <div className="space-y-4">
      {aiPresetsLoading ? (
        <div>Loading...</div>
      ) : (
        <form onSubmit={savePresets} className="space-y-4 max-w-2xl">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm text-gray-600 flex items-center gap-1">
                Provider <Tooltip text="Default AI provider" />
              </label>
              <input
                className="border rounded px-2 py-1"
                placeholder="openai"
                value={aiPresets.provider ?? ""}
                onChange={(e) =>
                  setAIPresets((p) => ({ ...p, provider: e.target.value }))
                }
              />
              <Tooltip text={`source: ${providerSource || "none"}`}>
                <span className="text-xs text-gray-500">
                  effective: {effectiveProvider || ""}
                </span>
              </Tooltip>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-gray-600 flex items-center gap-1">
                Model <Tooltip text="Default model name" />
              </label>
              <input
                className="border rounded px-2 py-1"
                placeholder="gpt-4o-mini"
                value={aiPresets.model ?? ""}
                onChange={(e) =>
                  setAIPresets((p) => ({ ...p, model: e.target.value }))
                }
              />
              <Tooltip text={`source: ${modelSource || "none"}`}>
                <span className="text-xs text-gray-500">
                  effective: {effectiveModel || ""}
                </span>
              </Tooltip>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-gray-600 flex items-center gap-1">
                Temperature (0..2) <Tooltip text="0 – deterministic, 2 – most random" />
              </label>
              <input
                className="border rounded px-2 py-1"
                type="number"
                step="0.1"
                min={0}
                max={2}
                value={aiPresets.temperature ?? 0}
                onChange={(e) =>
                  setAIPresets((p) => ({
                    ...p,
                    temperature: Number(e.target.value),
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1 md:col-span-2">
              <label className="text-sm text-gray-600 flex items-center gap-1">
                System prompt <Tooltip text="Added to every request" />
              </label>
              <textarea
                className="border rounded px-2 py-1 h-24"
                placeholder="You are helpful..."
                value={aiPresets.system_prompt ?? ""}
                onChange={(e) =>
                  setAIPresets((p) => ({
                    ...p,
                    system_prompt: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1 md:col-span-2">
              <label className="text-sm text-gray-600 flex items-center gap-1">
                Forbidden words <Tooltip text="List of disallowed words" />
              </label>
              {aiPresets.forbidden?.map((f, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <input
                    className="border rounded px-2 py-1 flex-1"
                    value={f}
                    onChange={(e) =>
                      setAIPresets((p) => {
                        const list = [...(p.forbidden ?? [])];
                        list[idx] = e.target.value;
                        return { ...p, forbidden: list };
                      })
                    }
                  />
                  <button
                    type="button"
                    className="px-2 py-1 rounded bg-red-200 dark:bg-red-800"
                    onClick={() =>
                      setAIPresets((p) => ({
                        ...p,
                        forbidden: (p.forbidden ?? []).filter((_, i) => i !== idx),
                      }))
                    }
                  >
                    Удалить
                  </button>
                </div>
              ))}
              <button
                type="button"
                className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800"
                onClick={() =>
                  setAIPresets((p) => ({
                    ...p,
                    forbidden: [...(p.forbidden ?? []), ""],
                  }))
                }
              >
                Добавить
              </button>
            </div>
          </div>
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

  const CHANNELS: NotificationChannel[] = [
    "in-app",
    "email",
    "webhook",
  ];

  const renderNotifications = () => (
    <div className="space-y-4">
      {notificationsLoading ? (
        <div>Loading...</div>
      ) : (
        <form onSubmit={saveNotificationsSettings} className="space-y-4">
          {(["achievement", "publish"] as const).map((trigger) => (
            <div key={trigger} className="flex flex-col gap-1">
              <div className="text-sm font-medium capitalize flex items-center gap-1">
                {trigger} <Tooltip text={`Delivery channels for ${trigger} event`} />
              </div>
              <div className="flex gap-4">
                {CHANNELS.map((ch) => (
                  <label
                    key={ch}
                    className="text-sm flex items-center gap-1"
                  >
                    <input
                      type="checkbox"
                      checked={notifications[trigger].includes(ch)}
                      onChange={(e) =>
                        setNotifications((n) => {
                          const set = new Set(n[trigger]);
                          if (e.target.checked) set.add(ch);
                          else set.delete(ch);
                          return { ...n, [trigger]: Array.from(set) };
                        })
                      }
                    />
                    {ch}
                  </label>
                ))}
              </div>
            </div>
          ))}
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
    <div className="space-y-4">
      {limitsLoading ? (
        <div>Loading...</div>
      ) : (
        <form onSubmit={saveLimitsSettings} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm text-gray-600 flex items-center gap-1">
                ai_tokens <Tooltip text="AI tokens limit" />
              </label>
              <input
                className="border rounded px-2 py-1"
                type="number"
                min={0}
                value={limits.ai_tokens}
                onChange={(e) =>
                  setLimitsState((l) => ({
                    ...l,
                    ai_tokens: Number(e.target.value),
                  }))
                }
              />
              <Tooltip text={`source: ${limitSource.ai_tokens}`}>
                <span className="text-xs text-gray-500">
                  effective: {effectiveLimits.ai_tokens}
                </span>
              </Tooltip>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-gray-600 flex items-center gap-1">
                notif_per_day <Tooltip text="Maximum notifications per day" />
              </label>
              <input
                className="border rounded px-2 py-1"
                type="number"
                min={0}
                value={limits.notif_per_day}
                onChange={(e) =>
                  setLimitsState((l) => ({
                    ...l,
                    notif_per_day: Number(e.target.value),
                  }))
                }
              />
              <Tooltip text={`source: ${limitSource.notif_per_day}`}>
                <span className="text-xs text-gray-500">
                  effective: {effectiveLimits.notif_per_day}
                </span>
              </Tooltip>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-gray-600 flex items-center gap-1">
                compass_calls <Tooltip text="Requests to Compass" />
              </label>
              <input
                className="border rounded px-2 py-1"
                type="number"
                min={0}
                value={limits.compass_calls}
                onChange={(e) =>
                  setLimitsState((l) => ({
                    ...l,
                    compass_calls: Number(e.target.value),
                  }))
                }
              />
              <Tooltip text={`source: ${limitSource.compass_calls}`}>
                <span className="text-xs text-gray-500">
                  effective: {effectiveLimits.compass_calls}
                </span>
              </Tooltip>
            </div>
          </div>
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
          <div className="text-sm space-y-2">
            <p className="text-gray-500">
              Basic information about the workspace.
            </p>
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
        return (
          <div className="space-y-2">
            <p className="text-sm text-gray-500">
              Manage members and their roles.
            </p>
            {renderMembers()}
          </div>
        );
      case "AI-presets":
        return (
          <div className="space-y-2">
            <p className="text-sm text-gray-500">
              Configure default AI parameters.
            </p>
            {renderAIPresets()}
          </div>
        );
      case "Notifications":
        return (
          <div className="space-y-2">
            <p className="text-sm text-gray-500">
              Choose how events send notifications.
            </p>
            {renderNotifications()}
          </div>
        );
      case "Limits":
        return (
          <div className="space-y-2">
            <p className="text-sm text-gray-500">
              Set usage limits for this workspace.
            </p>
            {renderLimits()}
          </div>
        );
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
