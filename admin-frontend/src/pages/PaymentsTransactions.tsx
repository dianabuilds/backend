import { useState, useEffect, useCallback } from "react";
import { api } from "../api/client";
import CursorPager from "../components/CursorPager";
import ErrorBanner from "../components/ErrorBanner";
import DataTable, { Column } from "../components/DataTable";

type Tx = {
  id: string;
  user_id: string;
  gateway?: string | null;
  product_type: string;
  product_id?: string | null;
  currency?: string | null;
  gross_cents: number;
  fee_cents: number;
  net_cents: number;
  status: string;
  created_at?: string | null;
  meta?: any;
};

type CursorResp = {
  items: Tx[];
  next_cursor?: string | null;
};

export default function PaymentsTransactions() {
  const [gateway, setGateway] = useState<string>("");
  const [ptype, setPtype] = useState<string>("");
  const [user, setUser] = useState<string>("");
  const [limit, setLimit] = useState<number>(50);

  const [rows, setRows] = useState<Tx[]>([]);
  const [next, setNext] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const buildQuery = useCallback((cursor?: string | null) => {
    const qs = new URLSearchParams();
    if (gateway) qs.set("f_gateway", gateway);
    if (ptype) qs.set("f_product_type", ptype);
    if (user) qs.set("f_user_id", user);
    qs.set("limit", String(limit));
    if (cursor) qs.set("cursor", cursor);
    return qs.toString();
  }, [gateway, ptype, user, limit]);

  const loadFirst = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<any>(`/admin/payments/transactions_cursor?${buildQuery(null)}`);
      const data: CursorResp = res.data || { items: [], next_cursor: null };
      setRows(Array.isArray(data.items) ? data.items : []);
      setNext((data as any).next_cursor || null);
    } catch (e: any) {
      setError(e?.message || "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [buildQuery]);

  const loadMore = useCallback(async () => {
    if (!next) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<any>(`/admin/payments/transactions_cursor?${buildQuery(next)}`);
      const data: CursorResp = res.data || { items: [], next_cursor: null };
      const newItems = Array.isArray(data.items) ? data.items : [];
      setRows((prev) => [...prev, ...newItems]);
      setNext((data as any).next_cursor || null);
    } catch (e: any) {
      setError(e?.message || "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  }, [buildQuery, next]);

  useEffect(() => {
    loadFirst();
  }, [loadFirst]);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-lg font-semibold">Payments — Transactions</h1>
      <div className="rounded border p-3">
        <div className="text-sm text-gray-500 mb-2">Фильтры</div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
          <input className="rounded border px-2 py-1" placeholder="Gateway (slug)" value={gateway} onChange={(e) => setGateway(e.target.value)} />
          <input className="rounded border px-2 py-1" placeholder="Product type" value={ptype} onChange={(e) => setPtype(e.target.value)} />
          <input className="rounded border px-2 py-1" placeholder="User ID" value={user} onChange={(e) => setUser(e.target.value)} />
          <input className="rounded border px-2 py-1" type="number" min={1} max={100} value={limit} onChange={(e) => setLimit(parseInt(e.target.value || "50"))} />
          <button onClick={loadFirst} className="text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200">Применить</button>
        </div>
      </div>

      <div className="rounded border p-3">
        {loading && rows.length === 0 ? <div className="text-sm text-gray-500">Загрузка…</div> : null}
        {error ? <ErrorBanner message={error} /> : null}
        {(() => {
          const cols: Column<Tx>[] = [
            { key: "created_at", title: "Time", accessor: (t) => t.created_at || "-" },
            { key: "user_id", title: "User" },
            { key: "gateway", title: "Gateway", accessor: (t) => t.gateway || "-" },
            {
              key: "product",
              title: "Product",
              render: (t) => (
                <span>
                  {t.product_type}
                  {t.product_id ? `:${t.product_id}` : ""}
                </span>
              ),
            },
            {
              key: "amount",
              title: "Amount",
              render: (t) => (
                <span>
                  {(t.gross_cents / 100).toFixed(2)} {t.currency || "USD"}
                </span>
              ),
            },
            { key: "fee_cents", title: "Fee", render: (t) => (t.fee_cents / 100).toFixed(2) },
            { key: "net_cents", title: "Net", render: (t) => (t.net_cents / 100).toFixed(2) },
            {
              key: "meta",
              title: "Meta",
              render: (t) => (
                <details>
                  <summary className="text-blue-600 cursor-pointer hover:underline">Показать</summary>
                  <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs bg-gray-50 p-2 rounded">
                    {JSON.stringify(t.meta ?? {}, null, 2)}
                  </pre>
                </details>
              ),
            },
          ];
          return <DataTable<Tx> columns={cols} data={rows} rowKey={(r) => r.id} emptyText={loading ? "Загрузка…" : "Нет транзакций"} />;
        })()}

        <CursorPager hasMore={Boolean(next)} loading={loading} onLoadMore={loadMore} className="mt-3 flex justify-center" />
      </div>
    </div>
  );
}
