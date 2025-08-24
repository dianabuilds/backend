import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { addNote, closeCase, getCaseFull } from "../api/moderationCases";
import PageLayout from "./_shared/PageLayout";

export default function ModerationCase() {
  const { id } = useParams<{ id: string }>();
  const nav = useNavigate();
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [note, setNote] = useState("");

  const load = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await getCaseFull(id);
      setData(res);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const onAddNote = async () => {
    if (!id || !note.trim()) return;
    await addNote(id, note, true);
    setNote("");
    await load();
  };

  const onClose = async (resolution: "resolved" | "rejected") => {
    if (!id) return;
    const reason = prompt("Reason code or text (optional):") || undefined;
    await closeCase(id, resolution, reason, reason);
    nav("/moderation");
  };

  return (
    <PageLayout
      title="Moderation — Case"
      subtitle={id || ""}
      actions={
        <div className="flex gap-2">
          <button
            className="px-3 py-1 rounded bg-green-600 text-white"
            onClick={() => onClose("resolved")}
          >
            Resolve
          </button>
          <button
            className="px-3 py-1 rounded bg-red-600 text-white"
            onClick={() => onClose("rejected")}
          >
            Reject
          </button>
        </div>
      }
    >
      {loading && <div className="text-sm text-gray-500">Loading...</div>}
      {data && (
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2">
            <div className="rounded border p-3 mb-4">
              <h2 className="font-semibold mb-2">Details</h2>
              <div className="text-sm">
                <div>
                  <b>Type:</b> {data.case.type}
                </div>
                <div>
                  <b>Status:</b> {data.case.status}
                </div>
                <div>
                  <b>Priority:</b> {data.case.priority}
                </div>
                <div>
                  <b>Summary:</b> {data.case.summary}
                </div>
                <div>
                  <b>Target:</b> {data.case.target_type || "-"}{" "}
                  {data.case.target_id || ""}
                </div>
                <div>
                  <b>Labels:</b> {data.case.labels.join(", ")}
                </div>
              </div>
            </div>
            <div className="rounded border p-3">
              <h2 className="font-semibold mb-2">Notes</h2>
              <div className="flex gap-2 mb-2">
                <input
                  className="border rounded px-2 py-1 flex-1"
                  placeholder="Internal note"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                />
                <button
                  className="px-3 py-1 rounded bg-blue-600 text-white"
                  onClick={onAddNote}
                >
                  Add
                </button>
              </div>
              <div className="space-y-2">
                {data.notes.map((n: any) => (
                  <div key={n.id} className="border rounded p-2">
                    <div className="text-xs text-gray-500">
                      {new Date(n.created_at).toLocaleString()} —{" "}
                      {n.internal ? "internal" : "public"}
                    </div>
                    <div className="whitespace-pre-wrap">{n.text}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div>
            <div className="rounded border p-3">
              <h2 className="font-semibold mb-2">Timeline</h2>
              <ul className="text-sm space-y-2">
                {data.events.map((e: any) => (
                  <li key={e.id}>
                    <div className="text-xs text-gray-500">
                      {new Date(e.created_at).toLocaleString()}
                    </div>
                    <div>
                      <b>{e.kind}</b>{" "}
                      {e.payload ? JSON.stringify(e.payload) : ""}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </PageLayout>
  );
}
