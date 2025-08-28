import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client";

type JobDetails = {
  job: {
    id: string;
    status: string;
    created_at?: string | null;
    started_at?: string | null;
    finished_at?: string | null;
    created_by?: string | null;
    provider?: string | null;
    model?: string | null;
    params: any;
    result_quest_id?: string | null;
    result_version_id?: string | null;
    cost?: number | null;
    token_usage?: any;
    reused?: boolean;
    progress?: number;
    logs_inline?: string[] | null;
    error?: string | null;
  };
  stage_logs: Array<{
    stage: string;
    provider: string;
    model: string;
    prompt: string;
    raw_response: string;
    usage: { prompt?: number; completion?: number; total?: number } | null;
    cost: number | null;
    status: string;
    created_at?: string | null;
  }>;
  aggregates: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    cost: number;
  };
};

type ValidationResp = {
  version_id: string;
  report: {
    errors: number;
    warnings: number;
    items: Array<{
      level: string;
      code: string;
      message: string;
      node?: string | null;
    }>;
  };
};

export default function AIQuestJobDetails() {
  const nav = useNavigate();
  const { id = "" } = useParams();
  const queryClient = useQueryClient();

  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: ["ai-quests", "job-details", id],
    enabled: Boolean(id),
    queryFn: async () => {
      const res = await api.get<JobDetails>(
        `/admin/ai/quests/jobs/${encodeURIComponent(id)}/details`,
      );
      return res.data;
    },
    refetchOnWindowFocus: true,
    staleTime: 5_000,
  });

  const versionId = data?.job?.result_version_id || null;

  const {
    data: validation,
    isFetching: vFetching,
    refetch: refetchValidation,
  } = useQuery({
    queryKey: ["ai-quests", "validation", versionId],
    enabled: Boolean(versionId),
    queryFn: async () => {
      const res = await api.get<ValidationResp>(
        `/admin/ai/quests/versions/${encodeURIComponent(versionId!)}/validation`,
      );
      return res.data;
    },
    staleTime: 15_000,
    refetchOnWindowFocus: false,
  });

  const summary = useMemo(() => {
    if (!data) return null;
    return {
      status: data.job.status,
      provider: data.job.provider || "-",
      model: data.job.model || "-",
      cost: data.job.cost ?? data.aggregates.cost,
      tokens:
        data.job.token_usage?.total?.total ?? data.aggregates.total_tokens,
      progress: data.job.progress ?? null,
      reused: data.job.reused ?? false,
    };
  }, [data]);

  const recalcValidation = async () => {
    if (!versionId) return;
    await api.get<ValidationResp>(
      `/admin/ai/quests/versions/${encodeURIComponent(versionId)}/validation?recalc=true`,
    );
    await refetchValidation();
  };

  const reload = async () => {
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: ["ai-quests", "job-details", id],
      }),
      versionId
        ? queryClient.invalidateQueries({
            queryKey: ["ai-quests", "validation", versionId],
          })
        : Promise.resolve(),
    ]);
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2">
        <button
          className="text-sm text-blue-600 hover:underline"
          onClick={() => nav(-1)}
        >
          &larr; Назад
        </button>
        <h1 className="text-lg font-semibold">AI Quest — Детали задачи</h1>
        <button
          onClick={reload}
          className="ml-auto text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200"
        >
          Обновить
        </button>
      </div>

      {isLoading ? (
        <div className="text-sm text-gray-500">Загрузка…</div>
      ) : null}
      {error ? (
        <div className="text-sm text-red-600">
          Ошибка: {error instanceof Error ? error.message : String(error)}
        </div>
      ) : null}
      {data ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded border p-3">
              <div className="text-sm text-gray-500">Задача</div>
              <div className="mt-1 text-sm">
                <div>
                  <span className="text-gray-500">ID:</span> {data.job.id}
                </div>
                <div>
                  <span className="text-gray-500">Статус:</span>{" "}
                  <StatusBadge
                    status={summary?.status || "-"}
                    reused={summary?.reused}
                  />
                </div>
                <div>
                  <span className="text-gray-500">Провайдер:</span>{" "}
                  {summary?.provider}{" "}
                  <span className="ml-2 text-gray-500">Модель:</span>{" "}
                  {summary?.model}
                </div>
                <div>
                  <span className="text-gray-500">Создана:</span>{" "}
                  {data.job.created_at || "-"}{" "}
                  <span className="ml-2 text-gray-500">Начата:</span>{" "}
                  {data.job.started_at || "-"}{" "}
                  <span className="ml-2 text-gray-500">Завершена:</span>{" "}
                  {data.job.finished_at || "-"}
                </div>
                <div>
                  <span className="text-gray-500">Стоимость:</span> $
                  {Number(summary?.cost || 0).toFixed(4)}{" "}
                  <span className="ml-2 text-gray-500">Токены:</span>{" "}
                  {summary?.tokens ?? "-"}
                </div>
                {data.job.error ? (
                  <div className="text-red-600 break-words mt-2">
                    Ошибка: {data.job.error}
                  </div>
                ) : null}
              </div>
              <div className="mt-3 flex gap-2">
                {data.job.result_version_id && data.job.result_quest_id ? (
                  <Link
                    to={`/quests/${data.job.result_quest_id}/versions/${data.job.result_version_id}`}
                    className="text-sm px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700"
                  >
                    Открыть версию
                  </Link>
                ) : null}
              </div>
            </div>

            <div className="rounded border p-3">
              <div className="text-sm text-gray-500">Агрегаты</div>
              <div className="mt-1 text-sm">
                <div>
                  <span className="text-gray-500">Prompt tokens:</span>{" "}
                  {data.aggregates.prompt_tokens}
                </div>
                <div>
                  <span className="text-gray-500">Completion tokens:</span>{" "}
                  {data.aggregates.completion_tokens}
                </div>
                <div>
                  <span className="text-gray-500">Всего токенов:</span>{" "}
                  {data.aggregates.total_tokens}
                </div>
                <div>
                  <span className="text-gray-500">Суммарная стоимость:</span> $
                  {data.aggregates.cost.toFixed(4)}
                </div>
              </div>
              {versionId ? (
                <div className="mt-3">
                  <div className="text-sm text-gray-500 mb-1">
                    Валидация версии
                  </div>
                  {vFetching ? (
                    <div className="text-xs text-gray-500">
                      Загрузка отчёта…
                    </div>
                  ) : null}
                  {validation ? (
                    <div className="text-sm">
                      <div>
                        Ошибок:{" "}
                        <span
                          className={
                            validation.report.errors > 0
                              ? "text-red-600"
                              : "text-green-600"
                          }
                        >
                          {validation.report.errors}
                        </span>
                        , предупреждений:{" "}
                        <span className="text-yellow-600">
                          {validation.report.warnings}
                        </span>
                      </div>
                      <details className="mt-2">
                        <summary className="cursor-pointer text-gray-700">
                          Показать детали
                        </summary>
                        <ul className="mt-2 list-disc pl-5 space-y-1">
                          {validation.report.items.map((it, idx) => (
                            <li
                              key={idx}
                              className={
                                it.level === "error"
                                  ? "text-red-600"
                                  : "text-yellow-700"
                              }
                            >
                              [{it.level}] {it.code}: {it.message}
                              {it.node ? ` (node=${it.node})` : ""}
                            </li>
                          ))}
                        </ul>
                      </details>
                    </div>
                  ) : null}
                  <button
                    onClick={recalcValidation}
                    className="mt-2 text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200"
                  >
                    Пересчитать
                  </button>
                </div>
              ) : null}
            </div>
          </div>

          <div className="rounded border p-3">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500">Стадии генерации</div>
              {isFetching ? (
                <div className="text-xs text-gray-500">Обновление…</div>
              ) : null}
            </div>
            <div className="mt-2 overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500">
                    <th className="px-2 py-1">Stage</th>
                    <th className="px-2 py-1">Provider/Model</th>
                    <th className="px-2 py-1">Tokens</th>
                    <th className="px-2 py-1">Cost</th>
                    <th className="px-2 py-1">Created</th>
                    <th className="px-2 py-1">Raw</th>
                  </tr>
                </thead>
                <tbody>
                  {data.stage_logs.map((s, idx) => (
                    <tr key={idx} className="border-t">
                      <td className="px-2 py-1">{s.stage}</td>
                      <td className="px-2 py-1">
                        {s.provider} / {s.model}
                      </td>
                      <td className="px-2 py-1">
                        {s.usage
                          ? `${s.usage.prompt ?? 0} + ${s.usage.completion ?? 0} = ${s.usage.total ?? (s.usage.prompt ?? 0) + (s.usage.completion ?? 0)}`
                          : "-"}
                      </td>
                      <td className="px-2 py-1">
                        ${Number(s.cost || 0).toFixed(4)}
                      </td>
                      <td className="px-2 py-1">{s.created_at || "-"}</td>
                      <td className="px-2 py-1">
                        <details>
                          <summary className="text-blue-600 cursor-pointer hover:underline">
                            Показать
                          </summary>
                          <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs bg-gray-50 p-2 rounded">
                            {s.raw_response}
                          </pre>
                        </details>
                      </td>
                    </tr>
                  ))}
                  {data.stage_logs.length === 0 ? (
                    <tr>
                      <td
                        className="px-2 py-3 text-gray-500 text-sm"
                        colSpan={6}
                      >
                        Логи стадий отсутствуют
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}

function StatusBadge({ status, reused }: { status: string; reused?: boolean }) {
  const map: Record<string, string> = {
    queued: "bg-gray-200 text-gray-800",
    running: "bg-blue-200 text-blue-800",
    completed: "bg-green-200 text-green-800",
    failed: "bg-red-200 text-red-800",
    canceled: "bg-yellow-200 text-yellow-800",
  };
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className={`px-2 py-0.5 rounded text-xs ${map[status] || "bg-gray-200"}`}
      >
        {status}
      </span>
      {reused ? (
        <span className="px-2 py-0.5 rounded text-xs bg-purple-200 text-purple-800">
          cache
        </span>
      ) : null}
    </span>
  );
}
