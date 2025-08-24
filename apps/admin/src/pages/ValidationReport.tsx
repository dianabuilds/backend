import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../api/client";
import ValidationReportView from "../components/ValidationReportView";
import PageLayout from "./_shared/PageLayout";

export default function ValidationReport() {
  const { type, id } = useParams<{ type: string; id: string }>();
  const [report, setReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!type || !id) return;
    setLoading(true);
    try {
      const res = await api.post(
        `/admin/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}/validate`,
      );
      setReport(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    run();
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
        <ValidationReportView report={report} />
      </div>
    </PageLayout>
  );
}
