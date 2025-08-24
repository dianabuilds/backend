import { useEffect, useState } from "react";

import WorkspaceSelector from "../components/WorkspaceSelector";
import { simulatePreview } from "../api/preview";
import { useWorkspace } from "../workspace/WorkspaceContext";

export default function Preview() {
  const { workspaceId } = useWorkspace();

  const [start, setStart] = useState("");
  const [previewMode, setPreviewMode] = useState("off");
  const [role, setRole] = useState("");
  const [plan, setPlan] = useState("");
  const [seed, setSeed] = useState<string>("");
  const [locale, setLocale] = useState("");
  const [device, setDevice] = useState("");
  const [time, setTime] = useState("");

  const [current, setCurrent] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [trace, setTrace] = useState<unknown[]>([]);
  const [reason, setReason] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [autoRunning, setAutoRunning] = useState(false);
  const [tab, setTab] = useState<"preview" | "trace">("preview");

  useEffect(() => {
    if (history.length === 0) setCurrent(start);
  }, [start, history.length]);

  const path = [...history, current].filter(Boolean);

  const reset = () => {
    setHistory([]);
    setCurrent(start);
    setTrace([]);
    setReason(null);
    setError(null);
  };

  const call = async (slug: string) => {
    if (!workspaceId || !slug) return null;
    setError(null);
    try {
      const res = await simulatePreview({
        workspace_id: workspaceId,
        start: slug,
        history,
        preview_mode: previewMode,
        role: role || undefined,
        plan: plan || undefined,
        seed: seed ? Number(seed) : undefined,
        locale: locale || undefined,
        device: device || undefined,
        time: time || undefined,
      });
      setTrace(res.trace || []);
      setReason(res.reason ?? null);
      return res.next ?? null;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      return null;
    }
  };

  const step = async () => {
    const slug = current.trim();
    if (!slug) return;
    const next = await call(slug);
    if (next) {
      setHistory((h) => [...h, slug]);
      setCurrent(next);
    }
  };

  const autoRun = async () => {
    setAutoRunning(true);
    try {
      let slug = current.trim();
      while (slug) {
        const next = await call(slug);
        if (!next) break;
        setHistory((h) => [...h, slug]);
        slug = next;
        setCurrent(next);
      }
    } finally {
      setAutoRunning(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
        <label className="flex flex-col gap-1">
          <span className="text-sm text-gray-600">Workspace</span>
          <WorkspaceSelector />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-gray-600">Start node/quest</span>
          <input
            value={start}
            onChange={(e) => setStart(e.target.value)}
            className="border rounded px-2 py-1"
            placeholder="start-slug"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-gray-600">Preview mode</span>
          <select
            value={previewMode}
            onChange={(e) => setPreviewMode(e.target.value)}
            className="border rounded px-2 py-1"
          >
            <option value="off">off</option>
            <option value="read_only">read_only</option>
            <option value="dry_run">dry_run</option>
            <option value="shadow">shadow</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-gray-600">Role</span>
          <input
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="border rounded px-2 py-1"
            placeholder="role"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-gray-600">Plan</span>
          <input
            value={plan}
            onChange={(e) => setPlan(e.target.value)}
            className="border rounded px-2 py-1"
            placeholder="plan"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-gray-600">Seed</span>
          <input
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            className="border rounded px-2 py-1"
            placeholder="123"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-gray-600">Locale</span>
          <input
            value={locale}
            onChange={(e) => setLocale(e.target.value)}
            className="border rounded px-2 py-1"
            placeholder="en"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-gray-600">Device</span>
          <input
            value={device}
            onChange={(e) => setDevice(e.target.value)}
            className="border rounded px-2 py-1"
            placeholder="web"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm text-gray-600">Time</span>
          <input
            value={time}
            onChange={(e) => setTime(e.target.value)}
            className="border rounded px-2 py-1"
            placeholder="2024-01-01T00:00:00Z"
          />
        </label>
      </div>

      <div className="flex gap-2">
        <button
          onClick={step}
          disabled={!workspaceId || !current}
          className="px-3 py-1 rounded border"
        >
          Step
        </button>
        <button
          onClick={autoRun}
          disabled={!workspaceId || !current || autoRunning}
          className="px-3 py-1 rounded border"
        >
          {autoRunning ? "Running..." : "Auto-run"}
        </button>
        <button onClick={reset} className="px-3 py-1 rounded border">
          Reset
        </button>
      </div>

      {error && <p className="text-red-600">{error}</p>}

      <div>
        <div className="flex gap-4 border-b mb-2">
          <button
            onClick={() => setTab("preview")}
            className={`pb-1 ${tab === "preview" ? "border-b-2 border-blue-500" : ""}`}
          >
            Preview
          </button>
          <button
            onClick={() => setTab("trace")}
            className={`pb-1 ${tab === "trace" ? "border-b-2 border-blue-500" : ""}`}
          >
            Trace
          </button>
        </div>
        {tab === "preview" ? (
          <div className="space-y-2">
            <div>Path: {path.join(" → ") || "-"}</div>
            {reason && <div className="text-sm text-gray-600">Reason: {reason}</div>}
          </div>
        ) : (
          <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
            {JSON.stringify(trace, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

