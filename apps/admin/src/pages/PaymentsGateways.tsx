import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";

type Gateway = {
  id: string;
  slug: string;
  type: string;
  enabled: boolean;
  priority: number;
  config: any;
  created_at?: string | null;
  updated_at?: string | null;
};

const TYPES = [
  { value: "crypto_jwt", label: "Crypto (JWT token placeholder)" },
  { value: "stripe_jwt", label: "Stripe (JWT token placeholder)" },
];

export default function PaymentsGateways() {
  const qc = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["payments", "gateways"],
    queryFn: async () =>
      (await api.get<Gateway[]>("/admin/payments/gateways")).data || [],
    staleTime: 10_000,
  });

  const [draft, setDraft] = useState<Partial<Gateway>>({
    slug: "",
    type: "crypto_jwt",
    enabled: true,
    priority: 100,
    config: {
      fee_mode: "percent",
      fee_percent: 0,
      fee_fixed_cents: 0,
      min_fee_cents: 0,
    },
  });

  const isEdit = Boolean(draft.id);

  const resetDraft = () =>
    setDraft({
      slug: "",
      type: "crypto_jwt",
      enabled: true,
      priority: 100,
      config: {
        fee_mode: "percent",
        fee_percent: 0,
        fee_fixed_cents: 0,
        min_fee_cents: 0,
      },
    });

  const save = async () => {
    if (!draft.slug || !draft.type) return alert("Slug и Type обязательны");
    const payload = {
      slug: draft.slug,
      type: draft.type,
      enabled: !!draft.enabled,
      priority: Number(draft.priority ?? 100),
      config: draft.config ?? {},
    };
    if (isEdit) {
      await api.put(
        `/admin/payments/gateways/${encodeURIComponent(draft.id!)}`,
        payload,
      );
    } else {
      await api.post(`/admin/payments/gateways`, payload);
    }
    resetDraft();
    await qc.invalidateQueries({ queryKey: ["payments", "gateways"] });
  };

  const remove = async (id: string) => {
    if (!confirm("Удалить шлюз?")) return;
    await api.del(`/admin/payments/gateways/${encodeURIComponent(id)}`);
    await qc.invalidateQueries({ queryKey: ["payments", "gateways"] });
  };

  const edit = (g: Gateway) => {
    setDraft({
      id: g.id,
      slug: g.slug,
      type: g.type,
      enabled: g.enabled,
      priority: g.priority,
      config: g.config || {},
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Fee helpers
  const setFee = (
    key: "fee_mode" | "fee_percent" | "fee_fixed_cents" | "min_fee_cents",
    value: string | number,
  ) => {
    setDraft((d) => ({ ...d, config: { ...(d.config || {}), [key]: value } }));
  };

  // Verify token
  const [verify, setVerify] = useState<{
    token: string;
    amount: number;
    currency: string;
    preferred_slug?: string;
  }>({
    token: "",
    amount: 100,
    currency: "USD",
    preferred_slug: "",
  });
  const [verifyRes, setVerifyRes] = useState<string>("");

  const doVerify = async () => {
    setVerifyRes("");
    try {
      const res = await api.post<{ ok: boolean; gateway?: string }>(
        `/admin/payments/verify`,
        {
          token: verify.token,
          amount: Number(verify.amount || 0),
          currency: verify.currency || null,
          preferred_slug: verify.preferred_slug || null,
        },
      );
      setVerifyRes(
        `ok=${(res.data as any)?.ok}, gateway=${(res.data as any)?.gateway || "-"}`,
      );
    } catch (e: any) {
      setVerifyRes(`Ошибка: ${e?.message || String(e)}`);
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-lg font-semibold">Payments — Gateways</h1>

      <div className="rounded border p-3">
        <div className="text-sm text-gray-500 mb-2">
          {isEdit ? "Редактирование шлюза" : "Создание шлюза"}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-gray-500">Slug</label>
            <input
              className="w-full rounded border px-2 py-1"
              value={draft.slug || ""}
              onChange={(e) => setDraft({ ...draft, slug: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Type</label>
            <select
              className="w-full rounded border px-2 py-1"
              value={draft.type || ""}
              onChange={(e) => setDraft({ ...draft, type: e.target.value })}
            >
              {TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500">Priority</label>
            <input
              className="w-full rounded border px-2 py-1"
              type="number"
              value={draft.priority ?? 100}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  priority: parseInt(e.target.value || "100", 10),
                })
              }
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              id="gw-enabled"
              type="checkbox"
              checked={!!draft.enabled}
              onChange={(e) =>
                setDraft({ ...draft, enabled: e.target.checked })
              }
            />
            <label htmlFor="gw-enabled" className="text-sm">
              Enabled
            </label>
          </div>

          <div className="md:col-span-3 grid grid-cols-1 md:grid-cols-4 gap-3 mt-2">
            <div>
              <label className="block text-xs text-gray-500">Fee mode</label>
              <select
                className="w-full rounded border px-2 py-1"
                value={(draft.config?.fee_mode as any) || "percent"}
                onChange={(e) => setFee("fee_mode", e.target.value)}
              >
                <option value="none">none</option>
                <option value="percent">percent</option>
                <option value="fixed">fixed</option>
                <option value="mixed">mixed</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500">Fee percent</label>
              <input
                className="w-full rounded border px-2 py-1"
                type="number"
                step="0.1"
                value={Number(draft.config?.fee_percent || 0)}
                onChange={(e) =>
                  setFee("fee_percent", parseFloat(e.target.value || "0"))
                }
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500">
                Fee fixed (cents)
              </label>
              <input
                className="w-full rounded border px-2 py-1"
                type="number"
                value={Number(draft.config?.fee_fixed_cents || 0)}
                onChange={(e) =>
                  setFee("fee_fixed_cents", parseInt(e.target.value || "0", 10))
                }
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500">
                Min fee (cents)
              </label>
              <input
                className="w-full rounded border px-2 py-1"
                type="number"
                value={Number(draft.config?.min_fee_cents || 0)}
                onChange={(e) =>
                  setFee("min_fee_cents", parseInt(e.target.value || "0", 10))
                }
              />
            </div>

            <div className="md:col-span-4">
              <label className="block text-xs text-gray-500">
                Config (JSON)
              </label>
              <textarea
                className="w-full rounded border px-2 py-1 font-mono text-xs min-h-[120px]"
                value={JSON.stringify(draft.config || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const v = JSON.parse(e.target.value || "{}");
                    setDraft((d) => ({ ...d, config: v }));
                  } catch {
                    // игнорируем при вводе; можно добавить подсветку ошибки
                  }
                }}
              />
            </div>
          </div>
        </div>
        <div className="mt-3 flex gap-2">
          <button
            onClick={save}
            className="text-sm px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700"
          >
            {isEdit ? "Сохранить" : "Создать"}
          </button>
          <button
            onClick={resetDraft}
            className="text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200"
          >
            Сбросить
          </button>
        </div>
      </div>

      <div className="rounded border p-3">
        <div className="text-sm text-gray-500 mb-2">Список шлюзов</div>
        {isLoading ? (
          <div className="text-sm text-gray-500">Загрузка…</div>
        ) : null}
        {error ? (
          <div className="text-sm text-red-600">{(error as any)?.message}</div>
        ) : null}
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="px-2 py-1">Slug</th>
                <th className="px-2 py-1">Type</th>
                <th className="px-2 py-1">Priority</th>
                <th className="px-2 py-1">Enabled</th>
                <th className="px-2 py-1">Fee</th>
                <th className="px-2 py-1">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(data || []).map((g) => (
                <tr key={g.id} className="border-t">
                  <td className="px-2 py-1">{g.slug}</td>
                  <td className="px-2 py-1">{g.type}</td>
                  <td className="px-2 py-1">{g.priority}</td>
                  <td className="px-2 py-1">{g.enabled ? "yes" : "no"}</td>
                  <td className="px-2 py-1">
                    {(() => {
                      const c = g.config || {};
                      const mode = c.fee_mode || "none";
                      const pct = Number(c.fee_percent || 0);
                      const fx = Number(c.fee_fixed_cents || 0);
                      return `${mode}${pct ? ` ${pct}%` : ""}${fx ? ` + ${fx}c` : ""}`;
                    })()}
                  </td>
                  <td className="px-2 py-1">
                    <button
                      onClick={() => edit(g)}
                      className="text-blue-600 hover:underline mr-2"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => remove(g.id)}
                      className="text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {(data || []).length === 0 ? (
                <tr>
                  <td className="px-2 py-3 text-gray-500" colSpan={6}>
                    Нет шлюзов
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded border p-3">
        <div className="text-sm text-gray-500 mb-2">Проверка токена</div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="md:col-span-2">
            <label className="block text-xs text-gray-500">Token (JWT)</label>
            <textarea
              className="w-full rounded border px-2 py-1 font-mono text-xs min-h-[80px]"
              value={verify.token}
              onChange={(e) =>
                setVerify((v) => ({ ...v, token: e.target.value }))
              }
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">
              Amount (cents)
            </label>
            <input
              className="w-full rounded border px-2 py-1"
              type="number"
              value={verify.amount}
              onChange={(e) =>
                setVerify((v) => ({
                  ...v,
                  amount: parseInt(e.target.value || "0", 10),
                }))
              }
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Currency</label>
            <input
              className="w-full rounded border px-2 py-1"
              value={verify.currency}
              onChange={(e) =>
                setVerify((v) => ({ ...v, currency: e.target.value }))
              }
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">
              Preferred slug (optional)
            </label>
            <input
              className="w-full rounded border px-2 py-1"
              value={verify.preferred_slug || ""}
              onChange={(e) =>
                setVerify((v) => ({ ...v, preferred_slug: e.target.value }))
              }
            />
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <button
            onClick={doVerify}
            className="text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200"
          >
            Проверить
          </button>
          {verifyRes ? <div className="text-sm">{verifyRes}</div> : null}
        </div>
      </div>
    </div>
  );
}
