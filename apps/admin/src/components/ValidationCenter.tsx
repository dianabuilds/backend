import { useEffect, useState } from "react";

import { api } from "../api/client";
import ValidationReportView from "./ValidationReportView";

type Props = {
  id: number;
};

export default function ValidationCenter({ id }: Props) {
  const [report, setReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const res = await api.post<void, { report?: unknown }>(
        `/content/${encodeURIComponent(String(id))}/validate`,
      );
      setReport(res.data?.report ?? null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    run();
  }, [id]);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold">Validation</h2>
        <button
          onClick={run}
          disabled={loading}
          className="px-2 py-1 text-sm rounded bg-blue-600 text-white disabled:opacity-50"
        >
          {loading ? "..." : "Re-run"}
        </button>
      </div>
      <ValidationReportView report={report} />
    </div>
  );
}
