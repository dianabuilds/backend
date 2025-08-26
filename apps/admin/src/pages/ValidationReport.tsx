import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../api/client";
import ValidationReportView from "../components/ValidationReportView";
import type { ValidationReport as ValidationReportModel } from "../openapi";
import PageLayout from "./_shared/PageLayout";

export default function ValidationReport() {
  const { type, id } = useParams<{ type: string; id: string }>();
  const [report, setReport] = useState<ValidationReportModel | null>(null);
  const [loading, setLoading] = useState(false);
  const [aiReport, setAiReport] = useState<ValidationReportModel | null>(null);
  const [aiLoading, setAiLoading] = useState(false);

  const run = async () => {
    if (!type || !id) return;
    setLoading(true);
    try {
      const res = await api.post(
        `/admin/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}/validate`,
      );
      setReport(res.data?.report ?? null);
    } finally {
      setLoading(false);
    }
  };

  const runAi = async () => {
    if (!type || !id) return;
    setAiLoading(true);
    try {
      const res = await api.post(
        `/admin/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}/validate_ai`,
      );
      setAiReport(res.data?.report ?? null);
    } finally {
      setAiLoading(false);
    }
  };

  useEffect(() => {
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type, id]);

  return (
    <PageLayout title="Validation report">
      <div className="space-y-2">
        <button
          className="px-2 py-1 text-sm rounded bg-blue-600 text-white disabled:opacity-50"
          onClick={run}
          disabled={loading}
        >
          {loading ? "..." : "Re-run"}
        </button>
        <button
          className="px-2 py-1 text-sm rounded bg-purple-600 text-white disabled:opacity-50"
          onClick={runAi}
          disabled={aiLoading}
        >
          {aiLoading ? "..." : "Validate with AI"}
        </button>
        <ValidationReportView report={report} />
        {aiReport && (
          <div className="mt-4">
            <h3 className="font-semibold">AI Issues</h3>
            <ValidationReportView report={aiReport} />
          </div>
        )}
      </div>
    </PageLayout>
  );
}
