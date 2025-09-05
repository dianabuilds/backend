import { useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { z } from "zod";

import { createCampaign, estimateCampaign } from "../../api/notifications";
import type { CampaignCreate, CampaignFilters } from "../../openapi";
import Modal from "../../shared/ui/Modal";
import { useToast } from "../ToastProvider";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function BroadcastForm({ isOpen, onClose }: Props) {
  const { addToast } = useToast();
  const qc = useQueryClient();
  const [bType, setBType] = useState<"system" | "info" | "warning" | "quest">(
    "system",
  );
  const [bTitle, setBTitle] = useState("");
  const [bMessage, setBMessage] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [role, setRole] = useState("");
  const [isActive, setIsActive] = useState("any");
  const [isPremium, setIsPremium] = useState("any");
  const [createdFrom, setCreatedFrom] = useState("");
  const [createdTo, setCreatedTo] = useState("");
  const [estimate, setEstimate] = useState<number | null>(null);
  const [errors, setErrors] = useState<{ title: string | null; message: string | null }>({
    title: null,
    message: null,
  });

  const schema = z.object({
    title: z.string().min(1, "Title required"),
    message: z.string().min(1, "Message required"),
  });

  const validate = () => {
    const res = schema.safeParse({ title: bTitle, message: bMessage });
    setErrors({
      title: res.success ? null : res.error.formErrors.fieldErrors.title?.[0] ?? null,
      message: res.success ? null : res.error.formErrors.fieldErrors.message?.[0] ?? null,
    });
    return res.success;
  };

  const payloadFilters = useMemo(() => {
    const f: CampaignFilters = {};
    if (role) f.role = role;
    if (isActive !== "any") f.is_active = isActive === "true";
    if (isPremium !== "any") f.is_premium = isPremium === "true";
    if (createdFrom) f.created_from = new Date(createdFrom).toISOString();
    if (createdTo) f.created_to = new Date(createdTo).toISOString();
    return f;
  }, [role, isActive, isPremium, createdFrom, createdTo]);

  const doDryRun = async () => {
    if (!validate()) return;
    try {
      const res = (await estimateCampaign(payloadFilters)) as {
        total_estimate?: number;
      };
      setEstimate(res.total_estimate ?? 0);
      addToast({
        title: "Estimated recipients",
        description: String(res.total_estimate ?? 0),
        variant: "info",
      });
    } catch (e) {
      addToast({
        title: "Dry-run failed",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  const doStart = async () => {
    if (!validate()) return;
    try {
      const payload: CampaignCreate = {
        title: bTitle,
        message: bMessage,
        type: bType,
        filters: payloadFilters,
      };
      await createCampaign(payload);
      setEstimate(null);
      setBTitle("");
      setBMessage("");
      addToast({ title: "Broadcast started", variant: "success" });
      qc.invalidateQueries({ queryKey: ["campaigns"] });
      onClose();
    } catch (e) {
      addToast({
        title: "Failed to start broadcast",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Start broadcast">
      <div className="flex flex-col gap-2">
        <div className="flex flex-col">
          <label className="text-sm text-gray-600">Title</label>
          <input
            className="border rounded px-2 py-1"
            value={bTitle}
            onChange={(e) => setBTitle(e.target.value)}
          />
          {errors.title && (
            <span className="text-xs text-red-600">{errors.title}</span>
          )}
        </div>
        <div className="flex flex-col">
          <label className="text-sm text-gray-600">Type</label>
          <select
            className="border rounded px-2 py-1"
            value={bType}
            onChange={(e) =>
              setBType(
                e.target.value as "system" | "info" | "warning" | "quest",
              )
            }
          >
            <option value="system">system</option>
            <option value="info">info</option>
            <option value="warning">warning</option>
            <option value="quest">quest</option>
          </select>
        </div>
        <div className="flex flex-col">
          <label className="text-sm text-gray-600">Message</label>
          <textarea
            className="border rounded px-2 py-1"
            rows={3}
            value={bMessage}
            onChange={(e) => setBMessage(e.target.value)}
          />
          {errors.message && (
            <span className="text-xs text-red-600">{errors.message}</span>
          )}
        </div>
        <button
          className="self-start text-sm text-blue-600"
          onClick={() => setShowAdvanced((v) => !v)}
        >
          {showAdvanced ? "Hide filters" : "Show filters"}
        </button>
        {showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div className="flex flex-col">
              <label className="text-sm text-gray-600">Role</label>
              <select
                className="border rounded px-2 py-1"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="">any</option>
                <option value="user">user</option>
                <option value="moderator">moderator</option>
                <option value="admin">admin</option>
              </select>
            </div>
            <div className="flex flex-col">
              <label className="text-sm text-gray-600">Active</label>
              <select
                className="border rounded px-2 py-1"
                value={isActive}
                onChange={(e) => setIsActive(e.target.value)}
              >
                <option value="any">any</option>
                <option value="true">true</option>
                <option value="false">false</option>
              </select>
            </div>
            <div className="flex flex-col">
              <label className="text-sm text-gray-600">Premium</label>
              <select
                className="border rounded px-2 py-1"
                value={isPremium}
                onChange={(e) => setIsPremium(e.target.value)}
              >
                <option value="any">any</option>
                <option value="true">true</option>
                <option value="false">false</option>
              </select>
            </div>
            <div className="flex flex-col">
              <label className="text-sm text-gray-600">Created from</label>
              <input
                type="datetime-local"
                className="border rounded px-2 py-1"
                value={createdFrom}
                onChange={(e) => setCreatedFrom(e.target.value)}
              />
            </div>
            <div className="flex flex-col">
              <label className="text-sm text-gray-600">Created to</label>
              <input
                type="datetime-local"
                className="border rounded px-2 py-1"
                value={createdTo}
                onChange={(e) => setCreatedTo(e.target.value)}
              />
            </div>
          </div>
        )}
        <div className="flex items-center gap-2 mt-2">
          <button className="px-3 py-1 rounded border" onClick={doDryRun}>
            Estimate
          </button>
          <button
            className="px-3 py-1 rounded bg-blue-600 text-white"
            onClick={doStart}
          >
            Start
          </button>
          {estimate !== null && (
            <span className="text-sm text-gray-600">
              Estimated recipients: {estimate}
            </span>
          )}
        </div>
      </div>
    </Modal>
  );
}
