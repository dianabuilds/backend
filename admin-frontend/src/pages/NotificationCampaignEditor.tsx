import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getDraftCampaign,
  updateDraftCampaign,
  sendDraftCampaign,
  type DraftCampaign,
} from "../api/notifications";
import { useToast } from "../components/ToastProvider";

export default function NotificationCampaignEditor() {
  const { id } = useParams();
  const { addToast } = useToast();
  const qc = useQueryClient();
  const { data: campaign } = useQuery({
    queryKey: ["draftCampaign", id],
    queryFn: () => getDraftCampaign(id!),
    enabled: !!id,
  });
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (campaign) {
      setTitle(campaign.title);
      setMessage(campaign.message);
    }
  }, [campaign]);

  if (!id) return <div className="p-4 text-sm">No ID</div>;
  if (!campaign) return <div className="p-4 text-sm">Loading...</div>;

  const save = async () => {
    try {
      await updateDraftCampaign(id, { title, message });
      addToast({ title: "Saved", variant: "success" });
      qc.invalidateQueries({ queryKey: ["draftCampaign", id] });
    } catch (e) {
      addToast({
        title: "Failed to save",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  const send = async () => {
    try {
      await sendDraftCampaign(id);
      addToast({ title: "Dispatched", variant: "success" });
      qc.invalidateQueries({ queryKey: ["draftCampaign", id] });
    } catch (e) {
      addToast({
        title: "Failed to dispatch",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Campaign Editor</h1>
      <div className="flex flex-col space-y-2">
        <label className="text-sm">Title</label>
        <input className="border rounded px-2 py-1" value={title} onChange={(e) => setTitle(e.target.value)} />
      </div>
      <div className="flex flex-col space-y-2">
        <label className="text-sm">Message</label>
        <textarea
          className="border rounded px-2 py-1"
          rows={5}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
      </div>
      <div className="flex gap-2">
        <button className="px-3 py-1 border rounded" onClick={save}>
          Save
        </button>
        <button className="px-3 py-1 border rounded" onClick={send}>
          Send
        </button>
      </div>
    </div>
  );
}
