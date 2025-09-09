import { useState } from 'react';

import { api } from '../api/client';
import ValidationReportView from './ValidationReportView';

type Props = {
  questId: string;
  onSuccess?: () => void;
};

type ValidationReport = {
  errors: number;
  warnings: number;
  items: {
    level: 'error' | 'warning';
    code: string;
    message: string;
    node?: string | null;
    hint?: string | null;
  }[];
};

export default function PublishButton({ questId, onSuccess }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ValidationReport | null>(null);

  const publish = async () => {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      await api.post(`/quests/${encodeURIComponent(questId)}/publish`);
      onSuccess?.();
      alert('Квест опубликован');
    } catch (e: unknown) {
      // Ожидаем detail: { code: "VALIDATION_FAILED", report: {...} }
      const err = e as { response?: { data?: { detail?: { code?: string; report?: unknown } } } };
      const detail = err?.response?.data?.detail ?? null;
      if (detail && detail.code === 'VALIDATION_FAILED') {
        setReport((detail.report as ValidationReport) || null);
      } else {
        setError((e as Error)?.message || 'Ошибка публикации');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <button
        onClick={publish}
        disabled={loading}
        className="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
      >
        {loading ? 'Публикую…' : 'Опубликовать'}
      </button>
      {error ? <div className="text-sm text-red-700">{error}</div> : null}
      {report ? (
        <div className="mt-2">
          <div className="text-sm font-semibold">Публикация заблокирована: ошибки валидации</div>
          <ValidationReportView report={report} />
        </div>
      ) : null}
    </div>
  );
}
