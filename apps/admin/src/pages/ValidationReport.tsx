import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { useAccount } from '../account/AccountContext';
import ValidationReportView from '../components/ValidationReportView';
// Local lightweight shape used by the UI component
type ValidationItem = { level: 'error' | 'warning'; code: string; message: string };
type ValidationReportModel = { errors: number; warnings: number; items: ValidationItem[] };
import PageLayout from './_shared/PageLayout';

export default function ValidationReport() {
  const { id } = useParams<{ id: string }>();
  const { accountId } = useAccount();
  const [report, setReport] = useState<ValidationReportModel | null>(null);
  const [loading, setLoading] = useState(false);
  const [aiReport, setAiReport] = useState<ValidationReportModel | null>(null);
  const [aiLoading, setAiLoading] = useState(false);

  const nodeId = Number(id);

  const run = async () => {
    if (!Number.isInteger(nodeId)) return;
    setLoading(true);
    try {
      // Endpoint not available. Keep no-op to avoid breaking the page.
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  const runAi = async () => {
    if (!Number.isInteger(nodeId)) return;
    setAiLoading(true);
    try {
      setAiReport(null);
    } finally {
      setAiLoading(false);
    }
  };

  useEffect(() => {
    void run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodeId, accountId]);

  return (
    <PageLayout title="Validation report">
      <div className="space-y-2">
        <button
          className="px-2 py-1 text-sm rounded bg-blue-600 text-white disabled:opacity-50"
          onClick={run}
          disabled={loading}
        >
          {loading ? '...' : 'Re-run'}
        </button>
        <button
          className="px-2 py-1 text-sm rounded bg-purple-600 text-white disabled:opacity-50"
          onClick={runAi}
          disabled={aiLoading}
        >
          {aiLoading ? '...' : 'Validate with AI'}
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
