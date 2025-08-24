import { useState } from "react";
import {
  simulateTransitions,
  type SimulateTransitionsBody,
  type SimulateTransitionsResponse,
} from "../api/transitions";

type Tab = "candidates" | "filters" | "scores" | "metrics" | "fallback";

export default function TransitionsTrace() {
  const [start, setStart] = useState("");
  const [mode, setMode] = useState("");
  const [seed, setSeed] = useState("");
  const [history, setHistory] = useState("");
  const [previewMode, setPreviewMode] = useState("off");

  const [result, setResult] = useState<SimulateTransitionsResponse | null>(null);
  const [tab, setTab] = useState<Tab>("candidates");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload: SimulateTransitionsBody = {
      start: start.trim(),
      preview_mode: previewMode,
    };
    if (mode.trim()) payload.mode = mode.trim();
    if (seed.trim()) {
      const num = Number(seed);
      if (!isNaN(num)) payload.seed = num;
    }
    const hist = history
      .split(/[,\s]+/)
      .map((s) => s.trim())
      .filter(Boolean);
    if (hist.length) payload.history = hist;
    setLoading(true);
    setError(null);
    try {
      const res = await simulateTransitions(payload);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const trace = result?.trace || [];
  const metrics = result?.metrics || {};
  const tabs: Tab[] = ["candidates", "filters", "scores", "metrics", "fallback"];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Transitions Trace</h1>
      <form onSubmit={handleSubmit} className="mb-4 flex flex-wrap items-end gap-2">
        <input
          value={start}
          onChange={(e) => setStart(e.target.value)}
          placeholder="start"
          className="border rounded px-2 py-1"
        />
        <input
          value={mode}
          onChange={(e) => setMode(e.target.value)}
          placeholder="mode"
          className="border rounded px-2 py-1"
        />
        <input
          value={seed}
          onChange={(e) => setSeed(e.target.value)}
          placeholder="seed"
          className="border rounded px-2 py-1 w-24"
        />
        <input
          value={history}
          onChange={(e) => setHistory(e.target.value)}
          placeholder="history (comma separated)"
          className="border rounded px-2 py-1"
        />
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
        <button type="submit" className="px-3 py-1 rounded border" disabled={loading}>
          Run
        </button>
      </form>
      {error && <div className="text-red-600 mb-2">{error}</div>}
      {loading && <p>Loading...</p>}
      {result && !loading && (
        <div>
          <div className="mb-2">
            <span className="mr-4">Next: {result.next || "-"}</span>
            {result.reason && (
              <span>Reason: {result.reason.toLowerCase()}</span>
            )}
          </div>
          <div className="mb-2 flex flex-wrap gap-2">
            {tabs.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                type="button"
                className={`px-3 py-1 rounded border ${
                  tab === t ? "bg-gray-200" : ""
                }`}
              >
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>
          {tab === "candidates" && (
            <table className="min-w-full text-sm">
              <thead>
                <tr>
                  <th className="border px-2 py-1 text-left">Policy</th>
                  <th className="border px-2 py-1 text-left">Candidates</th>
                </tr>
              </thead>
              <tbody>
                {trace.map((t, idx) => (
                  <tr key={idx}>
                    <td className="border px-2 py-1">{t.policy || "-"}</td>
                    <td className="border px-2 py-1">
                      {(t.candidates || []).join(", ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {tab === "filters" && (
            <table className="min-w-full text-sm">
              <thead>
                <tr>
                  <th className="border px-2 py-1 text-left">Policy</th>
                  <th className="border px-2 py-1 text-left">Filters</th>
                </tr>
              </thead>
              <tbody>
                {trace.map((t, idx) => (
                  <tr key={idx}>
                    <td className="border px-2 py-1">{t.policy || "-"}</td>
                    <td className="border px-2 py-1">
                      {(t.filters || []).join(", ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {tab === "scores" && (
            <table className="min-w-full text-sm">
              <thead>
                <tr>
                  <th className="border px-2 py-1 text-left">Policy</th>
                  <th className="border px-2 py-1 text-left">Scores</th>
                </tr>
              </thead>
              <tbody>
                {trace.map((t, idx) => (
                  <tr key={idx}>
                    <td className="border px-2 py-1">{t.policy || "-"}</td>
                    <td className="border px-2 py-1">
                      <pre className="whitespace-pre-wrap">
                        {JSON.stringify(t.scores || {}, null, 2)}
                      </pre>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {tab === "metrics" && (
            <table className="min-w-full text-sm">
              <thead>
                <tr>
                  <th className="border px-2 py-1 text-left">Metric</th>
                  <th className="border px-2 py-1 text-left">Value</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(metrics).map(([k, v]) => (
                  <tr key={k}>
                    <td className="border px-2 py-1">{k}</td>
                    <td className="border px-2 py-1">{String(v)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {tab === "fallback" && (
            <div>
              <table className="min-w-full text-sm mb-2">
                <thead>
                  <tr>
                    <th className="border px-2 py-1 text-left">Policy</th>
                    <th className="border px-2 py-1 text-left">Chosen</th>
                  </tr>
                </thead>
                <tbody>
                  {trace.map((t, idx) => (
                    <tr key={idx}>
                      <td className="border px-2 py-1">{t.policy || "-"}</td>
                      <td className="border px-2 py-1">{t.chosen || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {result.reason && (
                <div className="mt-2">Reason: {result.reason.toLowerCase()}</div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
