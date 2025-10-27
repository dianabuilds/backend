import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Spinner, Button, Badge } from "@ui";
import { SettingsLayout } from '@shared/settings/SettingsLayout';
import { WalletConnectionCard } from '@shared/settings/WalletConnectionCard';
import { apiGet } from '@shared/api/client';
import { extractErrorMessage } from '@shared/utils/errors';

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
  const navigate = useNavigate();

  const loadBilling = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await apiGet<Summary>('/v1/billing/me/summary');
      setSummary(s);
    } catch (err) {
      setSummary(null);
      setError(extractErrorMessage(err, 'Billing service is temporarily unavailable.'));
    }
    try {
      const h = await apiGet<HistoryResponse>('/v1/billing/me/history?limit=10');
      setHistory(h);
    } catch {
      setHistory(null);
    }
    setLoading(false);
  }, []);

  React.useEffect(() => {
    loadBilling();
  }, [loadBilling]);

  const plan = summary?.plan;
  const subscription = summary?.subscription;
  const payment = summary?.payment;
  const historyItems = history?.items || [];

  const planTitle = plan?.title || plan?.slug || 'Free plan';
  const planPrice = formatPrice(plan?.price_cents ?? null, plan?.currency);
  const subscriptionStatus = subscription?.status || 'inactive';
  const renewalLabel = subscription
    ? subscription.ends_at
        ? `Ends ${new Date(subscription.ends_at).toLocaleString()}`
        : subscription.auto_renew
            ? 'Renews automatically'
            : 'Manual renewal'
    : 'No subscription';
  const paymentLabel = payment?.title || payment?.mode || 'Manual payouts';

  const errorBanner = error ? (
    <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      <div className="flex items-start justify-between gap-3">
        <span>{error}</span>
        <Button size="sm" variant="ghost" color="neutral" onClick={loadBilling}>
          Retry
        </Button>
      </div>
    </div>
  ) : null;

  const sidePanel = loading ? (
    <Card className="flex items-center gap-2 p-5 text-sm text-gray-500">
      <Spinner size="sm" /> Loading summary...
    </Card>
  ) : (
    <>
      <Card className="space-y-4 rounded-3xl border border-white/60 bg-white/80 p-5 shadow-sm">
        <div className="flex items-start justify-between">
          <h2 className="text-sm font-semibold text-gray-700">Plan overview</h2>
          <Badge color="neutral" variant="soft">{subscriptionStatus}</Badge>
        </div>
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center justify-between">
            <span>Plan</span>
            <span className="font-medium text-gray-900">{planTitle}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Price</span>
            <span className="font-medium text-gray-900">{planPrice}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Renewal</span>
            <span className="font-medium text-gray-900">{renewalLabel}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Payment</span>
            <span className="font-medium text-gray-900">{paymentLabel}</span>
          </div>
        </div>
      </Card>
      <WalletConnectionCard onWalletChange={() => { void loadBilling(); }} />
      <Card className="space-y-4 rounded-3xl border border-white/60 bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700">Quick links</h2>
        <div className="space-y-2 text-sm text-gray-600">
          <p>Jump to related settings for contact details, security controls or notification channels.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button type="button" size="sm" variant="ghost" color="neutral" onClick={() => navigate('/profile')}>
            Profile
          </Button>
          <Button type="button" size="sm" variant="ghost" color="neutral" onClick={() => navigate('/settings/security')}>
            Security
          </Button>
          <Button type="button" size="sm" color="primary" onClick={() => navigate('/settings/notifications')}>
            Notifications
          </Button>
        </div>
      </Card>
    </>
  );

  const mainContent = loading ? (
    <Card className="flex items-center justify-center gap-3 p-6 text-sm text-gray-500">
      <Spinner size="sm" /> Loading billing information...
    </Card>
  ) : (
    <div className="flex flex-col gap-6">
      <Card className="space-y-4 rounded-3xl border border-white/60 bg-white/80 p-6 shadow-sm">
        <div>
          <h2 className="text-sm font-semibold text-gray-600">Current plan</h2>
          {subscription ? (
            <div className="mt-3 space-y-1">
              <div className="text-base font-medium text-gray-900">{planTitle}</div>
              <div className="text-sm text-gray-500">
                Status: {subscription.status}{' '}
                {subscription.auto_renew ? '(auto renew)' : '(manual renew)'}
              </div>
              <div className="text-sm text-gray-500">
                Started: {new Date(subscription.started_at).toLocaleString()}
                {subscription.ends_at && (
                  <> - Ends: {new Date(subscription.ends_at).toLocaleString()}</>
                )}
              </div>
              <div className="text-sm text-gray-600">Price: {planPrice}</div>
            </div>
          ) : (
            <div className="mt-2 text-sm text-gray-500">No active subscription yet.</div>
          )}
        </div>
        <div>
          <h2 className="text-sm font-semibold text-gray-600">Payment method</h2>
          <div className="mt-2 text-sm text-gray-500">
            {payment?.message || 'Currently we support only EVM (SIWE) wallets.'}
          </div>
        </div>
      </Card>

      <Card className="space-y-3 rounded-3xl border border-white/60 bg-white/80 p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-600">Recent invoices</h2>
        </div>
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
                {item.provider && <div className="text-xs text-gray-500">Provider: {item.provider}</div>}
              </div>
            ))}
          </div>
        )}
        <div className="text-xs text-gray-400">
          Card payments and detailed invoices will arrive once contracts are ready.
        </div>
      </Card>
    </div>
  );

  return (
    <SettingsLayout
      title="Billing"
      description="Check your current plan, payment method and invoice history."
      error={errorBanner}
      side={sidePanel}
    >
      {mainContent}
    </SettingsLayout>
  );
}



