import { useState } from "react";

import { applyMerge, dryRunMerge } from "../api/tags";
import PageLayout from "./_shared/PageLayout";

export default function TagMerge() {
  const [fromId, setFromId] = useState("");
  const [toId, setToId] = useState("");
  const [report, setReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDryRun = async () => {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const r = await dryRunMerge(fromId.trim(), toId.trim());
      setReport(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const onApply = async () => {
    const reason = prompt("Reason (optional):") || undefined;
    setLoading(true);
    try {
      const r = await applyMerge(fromId.trim(), toId.trim(), reason);
      setReport(r);
      alert("Merge applied");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageLayout
      title="Merge tags"
      subtitle="Объединение источника в целевой тег"
    >
      <div className="rounded border p-3 max-w-2xl">
        <div className="flex gap-2 items-center mb-3">
          <label className="w-24">From (UUID)</label>
          <input
            className="border rounded px-2 py-1 w-full"
            value={fromId}
            onChange={(e) => setFromId(e.target.value)}
            placeholder="from tag id"
          />
        </div>
        <div className="flex gap-2 items-center mb-3">
          <label className="w-24">To (UUID)</label>
          <input
            className="border rounded px-2 py-1 w-full"
            value={toId}
            onChange={(e) => setToId(e.target.value)}
            placeholder="to tag id"
          />
        </div>
        <div className="flex gap-2 mb-3">
          <button
            className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800"
            onClick={onDryRun}
            disabled={loading}
          >
            Dry‑run
          </button>
          <button
            className="px-3 py-1 rounded bg-red-600 text-white"
            onClick={onApply}
            disabled={loading || !report || (report?.errors?.length ?? 0) > 0}
          >
            Apply merge
          </button>
        </div>
        {loading && <div className="text-sm text-gray-500">Checking...</div>}
        {error && <div className="text-sm text-red-600">{error}</div>}
        {report && (
          <div className="text-sm">
            <div className="mb-2">
              <b>From:</b> {report.from?.name} ({report.from?.id})
            </div>
            <div className="mb-2">
              <b>To:</b> {report.to?.name} ({report.to?.id})
            </div>
            <div className="mb-2">
              <b>Content touched:</b> {report.content_touched}
            </div>
            <div className="mb-2">
              <b>Aliases moved:</b> {report.aliases_moved}
            </div>
            {Array.isArray(report.errors) && report.errors.length > 0 && (
              <div className="text-red-600">
                Errors: {report.errors.join("; ")}
              </div>
            )}
            {Array.isArray(report.warnings) && report.warnings.length > 0 && (
              <div className="text-yellow-600">
                Warnings: {report.warnings.join("; ")}
              </div>
            )}
          </div>
        )}
      </div>
    </PageLayout>
  );
}
