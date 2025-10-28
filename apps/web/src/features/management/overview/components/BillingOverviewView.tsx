import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, Download, Wallet, AlertTriangle, Activity } from '@icons';
import {
  Accordion,
  Badge,
  Button,
  Card,
  Skeleton,
  Table,
  Tabs,
  useToast,
  ApexChart,
} from '@ui';

import { useBillingOverview } from '../hooks/useBillingOverview';
import type { BillingOverviewResponse, BillingPayout } from '@shared/types/management';

type Delta = {
  value: number;
  percent: number | null;
  trend: 'up' | 'down' | 'neutral';
};

const centsToUsd = (value: number | null | undefined) => ((value ?? 0) / 100).toFixed(2);

const computeDelta = (current: number, previous: number): Delta => {
  const diff = current - previous;
  if (previous === 0) {
    return {
      value: diff,
      percent: null,
      trend: diff === 0 ? 'neutral' : diff > 0 ? 'up' : 'down',
    };
  }
  const percent = (diff / Math.abs(previous)) * 100;
  return {
    value: diff,
    percent,
    trend: diff === 0 ? 'neutral' : diff > 0 ? 'up' : 'down',
  };
};

const formatDelta = (delta: Delta) => {
  const sign = delta.value > 0 ? '+' : '';
  const percent =
    delta.percent == null
      ? '—'
      : `${delta.percent > 0 ? '+' : ''}${delta.percent.toFixed(1)}%`;
  return `${sign}${delta.value} (${percent})`;
};

const toCSV = (overview: BillingOverviewResponse, mode: 'net' | 'gross') => {
  const rows = overview.revenue.map((point) => {
    const net = Number(point.amount || 0);
    const gross = mode === 'gross' ? net * 1.05 : net;
    return `${point.day},${gross.toFixed(2)}`;
  });
  return ['date,amount', ...rows].join('\n');
};

const getPayoutLabel = (status?: string | null) => {
  const normalized = String(status || '').toLowerCase();
  if (['failed', 'error', 'declined'].includes(normalized)) return { label: 'Ошибка', color: 'error' as const };
  if (['pending', 'processing'].includes(normalized)) return { label: 'В ожидании', color: 'warning' as const };
  if (['succeeded', 'success', 'captured', 'completed'].includes(normalized)) return { label: 'Успешно', color: 'success' as const };
  return { label: normalized || '—', color: 'neutral' as const };
};

const renderKpiCard = (
  title: string,
  value: string,
  delta: Delta,
  onClick: () => void,
) => (
  <Card className="p-5 shadow-sm border border-gray-100 hover:border-primary-200 transition">
    <div className="flex items-start justify-between gap-3">
      <div>
        <div className="text-xs uppercase tracking-wide text-gray-500">{title}</div>
        <div className="mt-2 text-2xl font-semibold text-gray-900">{value}</div>
        <div className="mt-1 text-xs text-gray-500">
          {delta.percent == null ? (
            <span className="text-gray-400">Нет данных для сравнения</span>
          ) : (
            <span
              className={
                delta.trend === 'up'
                  ? 'text-emerald-600'
                  : delta.trend === 'down'
                    ? 'text-rose-500'
                    : 'text-gray-500'
              }
            >
              {formatDelta(delta)}
            </span>
          )}
        </div>
      </div>
      <Button
        size="xs"
        variant="ghost"
        className="inline-flex items-center gap-1"
        onClick={onClick}
      >
        <ArrowUpRight className="h-4 w-4" />
        Подробнее
      </Button>
    </div>
  </Card>
);

const RevenueChart: React.FC<{
  overview: BillingOverviewResponse;
}> = ({ overview }) => {
  const [mode, setMode] = React.useState<'net' | 'gross'>('net');
  const { pushToast } = useToast();

  const series = React.useMemo(() => {
    const points = overview.revenue;
    if (!points.length) return [];
    return [
      {
        name: mode === 'net' ? 'Net' : 'Gross',
        data: points.map((point) => ({
          x: point.day,
          y: mode === 'net' ? Number(point.amount || 0) : Number(point.amount || 0) * 1.05,
        })),
      },
    ];
  }, [mode, overview.revenue]);

  const options = React.useMemo(
    () => ({
      chart: {
        id: 'billing-revenue',
        toolbar: { show: false },
      },
      xaxis: {
        type: 'datetime' as const,
        labels: { format: 'dd MMM' },
      },
      stroke: { width: 2, curve: 'smooth' as const },
      dataLabels: { enabled: false },
      tooltip: {
        y: {
          formatter: (value: number) => `$${value.toFixed(2)}`,
        },
      },
    }),
    [],
  );

  const handleExport = React.useCallback(() => {
    if (!overview.revenue.length) {
      pushToast({ intent: 'info', description: 'Нет данных для экспорта' });
      return;
    }
    const csv = toCSV(overview, mode);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `billing-revenue-${mode}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }, [mode, overview, pushToast]);

  return (
    <Card className="p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-gray-900">Динамика выручки</h3>
          <p className="text-sm text-gray-500">Помесячный прогресс, доступны Net/Gross режимы.</p>
        </div>
        <div className="flex items-center gap-2">
          <Tabs
            items={[
              { key: 'net', label: 'Net' },
              { key: 'gross', label: 'Gross*' },
            ]}
            value={mode}
            onChange={(key) => setMode(key as 'net' | 'gross')}
          />
          <Button
            size="sm"
            variant="ghost"
            className="inline-flex items-center gap-1"
            onClick={handleExport}
          >
            <Download className="h-4 w-4" />
            Экспорт
          </Button>
        </div>
      </div>
      {series.length ? (
        <ApexChart
          type="area"
          height={260}
          series={series}
          options={{
            ...options,
            fill: {
              type: 'gradient' as const,
              gradient: { shadeIntensity: 0.7, opacityFrom: 0.6, opacityTo: 0.05 },
            },
          }}
        />
      ) : (
        <div className="flex h-[240px] items-center justify-center text-sm text-gray-500">
          Нет данных для отображения
        </div>
      )}
      {mode === 'gross' ? (
        <p className="text-xs text-gray-400">
          * В данном режиме используется приближённое значение Gross (Net × 1.05). Уточнённые данные появятся после интеграции с учётной системой.
        </p>
      ) : null}
    </Card>
  );
};

const SegmentGrid: React.FC<{ overview: BillingOverviewResponse }> = ({ overview }) => {
  const tokens = overview.subscriptions.tokens;
  const networks = overview.subscriptions.networks;

  if (!tokens.length && !networks.length) {
    return null;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {tokens.length ? (
        <Card className="p-5 space-y-3">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Сегменты по токенам</h3>
            <p className="text-xs text-gray-500">Токен → активные подписки и MRR (USD).</p>
          </div>
          <div className="space-y-2">
            {tokens.map((token) => (
              <div key={token.token} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <Badge color="primary">{token.token.toUpperCase()}</Badge>
                  <span className="text-gray-600">подписок: {token.total}</span>
                </div>
                <span className="font-medium text-gray-900">${token.mrr_usd.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {networks.length ? (
        <Card className="p-5 space-y-3">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Сегменты по сетям</h3>
            <p className="text-xs text-gray-500">Распределение активных подписок по блокчейнам.</p>
          </div>
          <div className="space-y-2">
            {networks.map((network) => (
              <div key={`${network.network}:${network.chain_id ?? 'unknown'}`} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <Badge color="neutral">{network.network}</Badge>
                  {network.chain_id ? <span className="text-gray-500">Chain ID: {network.chain_id}</span> : null}
                </div>
                <span className="font-medium text-gray-900">{network.total}</span>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </div>
  );
};

const NetworksTable: React.FC<{ overview: BillingOverviewResponse }> = ({ overview }) => {
  const networks = overview.subscriptions.networks;
  if (!networks.length) return null;

  return (
    <Card className="p-5 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">Сводка по сетям</h3>
        <span className="text-xs text-gray-500">Всего сетей: {networks.length}</span>
      </div>
      <Table.Table>
        <Table.THead>
          <Table.TR>
            <Table.TH>Сеть</Table.TH>
            <Table.TH>Chain ID</Table.TH>
            <Table.TH>Активных подписок</Table.TH>
          </Table.TR>
        </Table.THead>
        <Table.TBody>
          {networks.map((network) => (
            <Table.TR key={`${network.network}-${network.chain_id ?? 'unknown'}`}>
              <Table.TD>{network.network}</Table.TD>
              <Table.TD>{network.chain_id ?? '—'}</Table.TD>
              <Table.TD>{network.total}</Table.TD>
            </Table.TR>
          ))}
        </Table.TBody>
      </Table.Table>
    </Card>
  );
};

const PayoutTimeline: React.FC<{ payouts: BillingPayout[] }> = ({ payouts }) => {
  if (!payouts.length) {
    return (
      <Card className="p-5 text-sm text-gray-500">
        Нет инцидентов по выплатам — всё работает штатно.
      </Card>
    );
  }

  return (
    <Card className="p-5 space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-gray-900">Инциденты выплат</h3>
        <Badge color="warning">{payouts.length}</Badge>
      </div>
      <div className="space-y-3">
        {payouts.map((payout) => {
          const { label, color } = getPayoutLabel(payout.status);
          return (
            <div key={payout.id} className="rounded-lg border border-amber-100 bg-amber-50 p-3 text-sm text-amber-900">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                <span className="font-medium">{label}</span>
                <span className="text-xs text-amber-700">
                  {payout.created_at ? new Date(payout.created_at).toLocaleString() : '—'}
                </span>
              </div>
              <div className="mt-1 text-xs text-amber-800">
                Сеть: {payout.network || '—'} · Токен: {payout.token || payout.currency || '—'} · Сумма: ${centsToUsd(payout.gross_cents ?? 0)}
              </div>
              {payout.failure_reason ? (
                <div className="mt-1 text-xs text-amber-800">Причина: {payout.failure_reason}</div>
              ) : null}
              {payout.tx_hash ? (
                <div className="mt-1 text-xs">
                  TX Hash:{' '}
                  <a
                    className="text-primary-600 hover:underline"
                    href={`https://etherscan.io/tx/${payout.tx_hash}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {payout.tx_hash.slice(0, 10)}…
                  </a>
                </div>
              ) : null}
              <div className="mt-2">
                <Badge color={color}>{label}</Badge>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

export const BillingOverviewView: React.FC = () => {
  const navigate = useNavigate();
  const { overview, previousOverview, payouts, loading, error, refresh, clearError } = useBillingOverview();

  const kpiMetrics = React.useMemo(() => {
    const prev = previousOverview?.kpi ?? overview.kpi;
    return [
      {
        key: 'success',
        title: 'Успешные транзакции',
        value: overview.kpi.success,
        delta: computeDelta(overview.kpi.success, prev.success),
        onClick: () => navigate('/finance/billing/payments?tab=transactions&status=success'),
      },
      {
        key: 'errors',
        title: 'Ошибки',
        value: overview.kpi.errors,
        delta: computeDelta(overview.kpi.errors, prev.errors),
        onClick: () => navigate('/finance/billing/payments?tab=transactions&status=error'),
      },
      {
        key: 'pending',
        title: 'В ожидании',
        value: overview.kpi.pending,
        delta: computeDelta(overview.kpi.pending, prev.pending),
        onClick: () => navigate('/finance/billing/payments?tab=transactions&status=pending'),
      },
      {
        key: 'volume',
        title: 'Объём, $',
        value: Number(overview.kpi.volume_cents || 0) / 100,
        delta: computeDelta(
          Number(overview.kpi.volume_cents || 0) / 100,
          Number(prev.volume_cents || 0) / 100,
        ),
        onClick: () => navigate('/finance/billing/payments'),
      },
    ];
  }, [navigate, overview, previousOverview]);

  const contracts = overview.kpi.contracts;
  const failedPayouts = payouts.filter((item) => {
    const status = String(item.status || '').toLowerCase();
    return ['failed', 'error', 'declined'].includes(status);
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Billing Overview</h1>
          <p className="text-sm text-gray-500">Пульс финансовых метрик платформы, состояние сетей и недавние инциденты.</p>
        </div>
        <Button size="sm" onClick={() => void refresh()}>
          Обновить данные
        </Button>
      </div>

      {error ? (
        <Card className="border border-rose-200 bg-rose-50 p-4 text-sm text-rose-600">
          <div className="flex items-start justify-between gap-3">
            <span>{error}</span>
            <Button size="xs" variant="ghost" onClick={clearError}>
              Скрыть
            </Button>
          </div>
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {kpiMetrics.map((metric) =>
          loading ? (
            <Card key={metric.key} className="p-5">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="mt-3 h-6 w-32" />
              <Skeleton className="mt-2 h-3 w-20" />
            </Card>
          ) : (
            renderKpiCard(
              metric.title,
              metric.key === 'volume' ? `$${metric.value.toFixed(2)}` : metric.value.toLocaleString(),
              metric.delta,
              metric.onClick,
            )
          ),
        )}
      </div>

      <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
        <div className="space-y-6">
          <RevenueChart overview={overview} />
          <SegmentGrid overview={overview} />
          <NetworksTable overview={overview} />
          <PayoutTimeline payouts={failedPayouts.slice(0, 10)} />
        </div>

        <div className="space-y-4">
          <Card className="p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Wallet className="h-5 w-5 text-primary-500" />
              <h3 className="text-sm font-semibold text-gray-900">Контракты и сети</h3>
            </div>
            <div className="space-y-1 text-sm text-gray-700">
              <div>Всего контрактов: {contracts?.total ?? '—'}</div>
              <div>Активных: {contracts?.enabled ?? '—'}</div>
              <div>Тестовые сети: {contracts?.testnet ?? '—'}</div>
              <div>Основные сети: {contracts?.mainnet ?? '—'}</div>
            </div>
          </Card>

          <Card className="p-5 space-y-3">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-emerald-500" />
              <h3 className="text-sm font-semibold text-gray-900">Статус заявок</h3>
            </div>
            <Accordion title="В ожидании / Ошибки">
              <div className="space-y-1 text-sm text-gray-700">
                <div>В ожидании подтверждения: {overview.kpi.pending}</div>
                <div>Проблемные выплаты: {failedPayouts.length}</div>
                <div>Всего выплат в отчёте: {payouts.length}</div>
              </div>
            </Accordion>
          </Card>

          <Card className="p-5 text-xs text-gray-500">
            Данные обновляются в реальном времени после каждого подтверждения on-chain. Для детальной диагностики переходите в раздел «Payments».
          </Card>
        </div>
      </div>
    </div>
  );
};
