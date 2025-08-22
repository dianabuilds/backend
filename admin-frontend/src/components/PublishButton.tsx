import { useState } from "react";
import { api } from "../api/client";
import ValidationReportView from "./ValidationReportView";

type Props = {
  questId: string;
  onSuccess?: () => void;
};

export default function PublishButton({ questId, onSuccess }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<any | null>(null);

  const publish = async () => {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      await api.post(`/quests/${encodeURIComponent(questId)}/publish`);
      if (onSuccess) onSuccess();
      alert("Квест опубликован");
    } catch (e: any) {
      // Ожидаем detail: { code: "VALIDATION_FAILED", report: {...} }
      const detail = e?.response?.data?.detail ?? null;
      if (detail && detail.code === "VALIDATION_FAILED") {
        setReport(detail.report || null);
      } else {
        setError(e?.message || "Ошибка публикации");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <button onClick={publish} disabled={loading} className="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 disabled:opacity-50">
        {loading ? "Публикую…" : "Опубликовать"}
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
