import { useState } from "react";
import { Link } from "react-router-dom";

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
    const initialCandidates = trace[0]?.candidates ?? [];
    const filters = trace.flatMap((t) => t.filters || []);
    content = (
      <div className="space-y-4">
        <details className="border rounded">
          <summary className="cursor-pointer px-2 py-1 font-semibold">
            Input context
          </summary>
          <div className="px-2 py-1 text-sm space-y-1">
            <div>Start: {start}</div>
            {mode && <div>Mode: {mode}</div>}
          </div>
        </details>
        <details className="border rounded">
          <summary className="cursor-pointer px-2 py-1 font-semibold">
            Candidates before filters
          </summary>
          <div className="px-2 py-1 text-sm">
            {initialCandidates.length ? (
              <ul className="list-disc pl-4">
                {initialCandidates.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            ) : (
              <div>-</div>
            )}
          </div>
        </details>
        <details className="border rounded">
          <summary className="cursor-pointer px-2 py-1 font-semibold">
            Scope filters
          </summary>
          <div className="px-2 py-1 text-sm">
            {filters.length ? (
              <ul className="list-disc pl-4">
                {filters.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            ) : (
              <div>-</div>
            )}
          </div>
        </details>
        <details className="border rounded">
          <summary className="cursor-pointer px-2 py-1 font-semibold">
            Scoring
          </summary>
          <div className="px-2 py-1 text-sm">
            {trace.length ? (
              trace.map((t, idx) => (
                <div key={idx} className="mb-2">
                  {t.policy && (
                    <div className="font-medium mb-1">{t.policy}</div>
                  )}
                  <pre className="whitespace-pre-wrap">
                    {JSON.stringify(t.scores || {}, null, 2)}
                  </pre>
                </div>
              ))
            ) : (
              <div>-</div>
            )}
          </div>
        </details>
        <details className="border rounded" open>
          <summary className="cursor-pointer px-2 py-1 font-semibold">
            Final selection
          </summary>
          <div className="px-2 py-1 text-sm space-y-2">
            <div>Next: {result?.next || "-"}</div>
            {result?.reason && (
              <div>Reason: {result.reason.toLowerCase()}</div>
            )}
            <Link
              to={`/transitions?from_slug=${encodeURIComponent(
                start.trim(),
              )}&to_slug=${encodeURIComponent(result?.next || "")}`}
              className="px-3 py-1 rounded border inline-block"
            >
              Apply changes in Transitions
            </Link>
          </div>
        </details>
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

