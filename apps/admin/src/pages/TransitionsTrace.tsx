import { useState } from "react";

import {
  simulateTransitions,
  type SimulateTransitionsResponse,
} from "../api/transitions";

type Step = 1 | 2 | 3;

export default function TransitionsTrace() {
  const [step, setStep] = useState<Step>(1);
  const [start, setStart] = useState("");
  const [mode, setMode] = useState("");
  const [result, setResult] = useState<SimulateTransitionsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await simulateTransitions({
        start: start.trim(),
        mode: mode.trim() || undefined,
      });
      setResult(res);
      setStep(3);
    } catch (e: any) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStep(1);
    setStart("");
    setMode("");
    setResult(null);
    setError(null);
  };

  let content: JSX.Element | null = null;
  if (step === 1) {
    content = (
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (start.trim()) setStep(2);
        }}
        className="flex items-center gap-2"
      >
        <input
          value={start}
          onChange={(e) => setStart(e.target.value)}
          placeholder="start node"
          className="border rounded px-2 py-1"
        />
        <button type="submit" className="px-3 py-1 rounded border" disabled={!start.trim()}>
          Next
        </button>
      </form>
    );
  } else if (step === 2) {
    content = (
      <form
        onSubmit={(e) => {
          e.preventDefault();
          run();
        }}
        className="flex items-center gap-2"
      >
        <input
          value={mode}
          onChange={(e) => setMode(e.target.value)}
          placeholder="mode"
          className="border rounded px-2 py-1"
        />
        <button type="submit" className="px-3 py-1 rounded border" disabled={loading}>
          Run
        </button>
        <button type="button" className="px-3 py-1 rounded border" onClick={reset}>
          Back
        </button>
      </form>
    );
  } else if (step === 3) {
    const trace = result?.trace || [];
    content = (
      <div className="space-y-4">
        <div>
          <span className="mr-4">Next: {result?.next || "-"}</span>
          {result?.reason && <span>Reason: {result.reason.toLowerCase()}</span>}
        </div>
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
                  {(t.candidates || []).join(", ") || "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <button
          type="button"
          className="px-3 py-1 rounded border"
          onClick={reset}
        >
          Start over
        </button>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Transitions Trace</h1>
      {error && <div className="text-red-600 mb-2">{error}</div>}
      {loading && <div className="mb-2">Loading...</div>}
      {content}
    </div>
  );
}

