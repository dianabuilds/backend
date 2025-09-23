import React from 'react';
import { Card, Spinner } from '../../shared/ui';
import { apiGet } from '../../shared/api/client';

interface Summary {
  plan: {
    id: string;
    slug: string;
    title: string;
    price_cents: number | null;
    currency: string | null;
    features?: Record<string, any> | null;
  } | null;
  subscription: {
    plan_id: string;
    status: string;
    auto_renew: boolean;
    started_at: string;
    ends_at?: string | null;
  } | null;
  payment: {
    mode: string;
    title: string;
    message: string;
    coming_soon?: boolean;
  };
}

interface HistoryResponse {
  items: Array<{
    id?: string;
    status?: string;
    created_at?: string;
    amount?: number | null;
    currency?: string | null;
    provider?: string | null;
    product_type?: string | null;
  }>;
  coming_soon?: boolean;
}

function formatPrice(priceCents: number | null, currency?: string | null): string {
  if (priceCents == null) return 'Free';
  const value = priceCents / 100;
  return `${value.toFixed(2)} ${currency || 'USD'}`;
}

export default function BillingPage() {
  const [summary, setSummary] = React.useState<Summary | null>(null);
  const [history, setHistory] = React.useState<HistoryResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const s = await apiGet<Summary>('/v1/billing/me/summary');
        setSummary(s);
      } catch (err: any) {
        setError(err?.message || 'Failed to load billing summary');
      }
      try {
        const h = await apiGet<HistoryResponse>('/v1/billing/me/history?limit=20');
        setHistory(h);
      } catch {}
      setLoading(false);
    })();
  }, []);

  const plan = summary?.plan;
  const subscription = summary?.subscription;
  const payment = summary?.payment;
  const historyItems = history?.items || [];

  return (
    <div className="grid gap-4">
      <h1 className="text-xl font-semibold text-gray-700">Billing</h1>
      {loading ? (
        <Card className="p-4 flex items-center gap-2 text-sm text-gray-500">
          <Spinner size="sm" /> Loading billing information…
        </Card>
      ) : (
        <>
          {error && <div className="text-error text-sm">{error}</div>}
          <Card className="p-5 space-y-4">
            <div>
              <h2 className="text-sm font-semibold text-gray-600">Current plan</h2>
              {subscription ? (
                <div className="mt-2">
                  <div className="text-base font-medium">{plan?.title || plan?.slug || 'Plan'}</div>
                  <div className="text-sm text-gray-500">
                    Status: {subscription.status}{' '}
                    {subscription.auto_renew ? '(auto renew)' : '(manual renew)'}
                  </div>
                  <div className="text-sm text-gray-500">
                    Started: {new Date(subscription.started_at).toLocaleString()}
                    {subscription.ends_at && (
                      <> · Ends: {new Date(subscription.ends_at).toLocaleString()}</>
                    )}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    Price: {formatPrice(plan?.price_cents ?? null, plan?.currency)}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-500">No active subscription yet.</div>
              )}
            </div>
            <div>
              <h2 className="text-sm font-semibold text-gray-600">Payment method</h2>
              <div className="mt-2 text-sm text-gray-500">
                {payment?.message || 'Currently we support only EVM (SIWE) wallets.'}
              </div>
            </div>
          </Card>

          <Card className="p-5 space-y-3">
            <h2 className="text-sm font-semibold text-gray-600">Recent invoices</h2>
            {history?.coming_soon ? (
              <div className="text-sm text-gray-500">History will appear once billing transactions are live.</div>
            ) : historyItems.length === 0 ? (
              <div className="text-sm text-gray-500">No billing history yet.</div>
            ) : (
              <div className="space-y-3">
                {historyItems.map((item) => (
                  <div key={item.id || item.created_at} className="rounded border border-gray-200 p-3">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium">{item.status || 'Transaction'}</span>
                      {item.created_at && (
                        <span className="text-gray-500">{new Date(item.created_at).toLocaleString()}</span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600">
                      {item.amount != null ? `${item.amount.toFixed(2)} ${item.currency || 'USD'}` : 'Amount pending'}
                    </div>
                    {item.provider && (
                      <div className="text-xs text-gray-500">Provider: {item.provider}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
            <div className="text-xs text-gray-400">Card payments and detailed invoices will arrive once contracts are ready.</div>
          </Card>
        </>
      )}
    </div>
  );
}

