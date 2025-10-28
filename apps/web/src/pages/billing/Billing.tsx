import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Spinner, Button, Badge } from "@ui";
import { SettingsLayout } from '@shared/settings/SettingsLayout';
import { WalletConnectionCard } from '@shared/settings/WalletConnectionCard';
import { shortenAddress } from '@shared/settings/useWalletConnection';
import {
  BillingGasInfo,
  BillingHistoryResponse,
  BillingSummary,
  fetchBillingHistory,
  fetchBillingSummary,
} from '@shared/api/billing';
import { extractErrorMessage } from '@shared/utils/errors';

function formatPrice(priceCents: number | null, currency?: string | null): string {
  if (priceCents == null) return 'Free';
  const value = priceCents / 100;
  return `${value.toFixed(2)} ${currency || 'USD'}`;
}

function formatAmountFromCents(amountCents?: number | null, currency?: string | null): string {
  if (amountCents == null) return '—';
  const value = amountCents / 100;
  return `${value.toFixed(2)} ${currency || 'USD'}`;
}

function shortenHash(hash?: string | null): string | null {
  if (!hash) return null;
  const trimmed = hash.trim();
  if (trimmed.length <= 14) return trimmed;
  return `${trimmed.slice(0, 8)}…${trimmed.slice(-6)}`;
}

function describeGas(gas?: BillingGasInfo | null): string | null {
  if (!gas) return null;
  const parts: string[] = [];
  const formatNumber = (value: number | null | undefined) => {
    if (value == null) return null;
    if (Math.abs(value) >= 1000) {
      return value.toLocaleString();
    }
    return value.toString();
  };
  const fee = formatNumber(gas.fee ?? null);
  if (fee) {
    const unit = gas.token || gas.currency || '';
    parts.push(unit ? `fee ${fee} ${unit}` : `fee ${fee}`);
  }
  const used = formatNumber(gas.used ?? null);
  if (used) {
    parts.push(`used ${used}`);
  }
  const price = formatNumber(gas.price ?? null);
  if (price) {
    parts.push(`price ${price}${gas.unit ? ` ${gas.unit}` : ''}`);
  }
  if (gas.note) {
    parts.push(gas.note);
  }
  return parts.length ? parts.join(' • ') : null;
}

export default function BillingPage() {
  const [summary, setSummary] = React.useState<BillingSummary | null>(null);
  const [history, setHistory] = React.useState<BillingHistoryResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const navigate = useNavigate();

  const loadBilling = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await fetchBillingSummary();
      setSummary(s);
    } catch (err) {
      setSummary(null);
      setError(extractErrorMessage(err, 'Billing service is temporarily unavailable.'));
    }
    try {
      const h = await fetchBillingHistory({ limit: 10 });
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
  const paymentStatus = payment?.status || null;
  const walletInfo = summary?.wallet ?? null;
  const walletAddress = walletInfo?.address ?? null;
  const walletStatus = walletAddress
    ? `${shortenAddress(walletAddress)}${walletInfo?.is_verified === false ? ' (unverified)' : ''}`
    : 'Not connected';
  const debt = summary?.debt ?? null;
  const outstandingLabel =
    debt?.is_overdue && debt?.amount_cents != null
      ? formatAmountFromCents(debt.amount_cents, debt.currency)
      : 'No outstanding balance';
  const outstandingTextClass = debt?.is_overdue ? 'text-rose-600' : 'text-gray-900';
  const lastPayment = summary?.last_payment ?? null;
  const lastPaymentStatus = lastPayment?.status || 'Not recorded';
  const lastPaymentStatusClass = (() => {
    const normalized = lastPaymentStatus.toLowerCase();
    if (normalized.includes('fail')) return 'text-rose-600';
    if (normalized.includes('pending') || normalized.includes('process')) return 'text-amber-600';
    if (normalized.includes('success') || normalized.includes('succeed') || normalized.includes('captured')) {
      return 'text-emerald-600';
    }
    return 'text-gray-700';
  })();
  const lastPaymentAmount =
    lastPayment?.amount_cents != null
      ? formatAmountFromCents(lastPayment.amount_cents, lastPayment.currency)
      : lastPayment?.amount != null
        ? `${lastPayment.amount.toFixed(2)} ${lastPayment.currency || 'USD'}`
        : null;
  const lastPaymentCreated = lastPayment?.created_at
    ? new Date(lastPayment.created_at).toLocaleString()
    : null;
  const lastPaymentNetwork = lastPayment?.network || null;
  const lastPaymentToken = lastPayment?.token || null;
  const lastPaymentHash = shortenHash(lastPayment?.tx_hash);
  const lastPaymentGas = describeGas(lastPayment?.gas ?? null);
  const lastPaymentFailure = lastPayment?.failure_reason || null;

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
          <div className="flex items-center justify-between">
            <span>Wallet</span>
            <span className="font-medium text-gray-900">{walletStatus}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Outstanding</span>
            <span className={`font-medium ${outstandingTextClass}`}>{outstandingLabel}</span>
          </div>
        </div>
      </Card>
      <WalletConnectionCard
        initialWalletAddress={walletAddress}
        initialWalletChainId={walletInfo?.chain_id ?? null}
        onWalletChange={() => { void loadBilling(); }}
      />
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
          {paymentStatus === 'wallet_missing' && (
            <div className="mt-1 text-xs text-rose-500">
              Connect an EVM wallet to enable payouts and invoice history.
            </div>
          )}
        </div>
        <div>
          <h2 className="text-sm font-semibold text-gray-600">Last payment</h2>
          {lastPayment ? (
            <div className="mt-2 space-y-1 text-sm text-gray-500">
              <div>
                Status:{' '}
                <span className={`font-medium ${lastPaymentStatusClass}`}>
                  {lastPaymentStatus}
                </span>
                {lastPaymentFailure && (
                  <span className="ml-1 text-xs text-rose-500">
                    ({lastPaymentFailure})
                  </span>
                )}
              </div>
              {lastPaymentCreated && (
                <div>Created: {lastPaymentCreated}</div>
              )}
              {lastPaymentAmount && (
                <div>Amount: {lastPaymentAmount}</div>
              )}
              <div className="text-xs text-gray-500">
                {lastPaymentNetwork && <span className="mr-3">Network: {lastPaymentNetwork}</span>}
                {lastPaymentToken && <span className="mr-3">Token: {lastPaymentToken}</span>}
                {lastPaymentHash && <span className="mr-3">Tx: {lastPaymentHash}</span>}
                {lastPaymentGas && <span>Gas: {lastPaymentGas}</span>}
              </div>
            </div>
          ) : (
            <div className="mt-2 text-sm text-gray-500">
              No payments recorded yet.
            </div>
          )}
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
            {historyItems.map((item) => {
              const statusText = item.status || 'Transaction';
              const normalized = statusText.toLowerCase();
              const statusClass = normalized.includes('fail')
                ? 'text-rose-600'
                : normalized.includes('pending') || normalized.includes('process')
                  ? 'text-amber-600'
                  : 'text-gray-900';
              const amountLabel =
                item.amount_cents != null
                  ? formatAmountFromCents(item.amount_cents, item.currency)
                  : item.amount != null
                    ? `${item.amount.toFixed(2)} ${item.currency || 'USD'}`
                    : 'Amount pending';
              const txHashLabel = shortenHash(item.tx_hash);
              const gasLabel = describeGas(item.gas ?? null);
              return (
                <div key={item.id || item.created_at} className="rounded border border-gray-200 p-3">
                  <div className="flex justify-between text-sm">
                    <span className={`font-medium ${statusClass}`}>{statusText}</span>
                    {item.created_at && (
                      <span className="text-gray-500">{new Date(item.created_at).toLocaleString()}</span>
                    )}
                  </div>
                  <div className="text-sm text-gray-600">
                    {amountLabel}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500">
                    {item.provider && <span>Provider: {item.provider}</span>}
                    {item.network && <span>Network: {item.network}</span>}
                    {item.token && <span>Token: {item.token}</span>}
                    {txHashLabel && <span>Tx: {txHashLabel}</span>}
                    {gasLabel && <span>Gas: {gasLabel}</span>}
                  </div>
                  {item.failure_reason && (
                    <div className="mt-1 text-xs text-rose-500">Failure: {item.failure_reason}</div>
                  )}
                </div>
              );
            })}
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



