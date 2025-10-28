import React from 'react';
import {
  Badge,
  Button,
  Card,
  Drawer,
  Input,
  Pagination,
  Select,
  Skeleton,
  Table,
  useToast,
} from '@ui';

import type {
  BillingContract,
  BillingProvider,
  BillingTransaction,
} from '@shared/types/management';
import type { BillingTransactionsParams } from '@shared/api/management/billing';

import {
  centsToUsd,
  formatDate,
  getTxStatusMeta,
  getNetworkOptions,
  txExplorerUrl,
} from '../helpers';

const PAGE_SIZE = 20;

type TransactionFilterState = {
  status: 'all' | 'succeeded' | 'failed' | 'pending';
  provider: string;
  contract: string;
  network: string;
  dateFrom: string;
  dateTo: string;
  amountMin: string;
  amountMax: string;
};

type TransactionsTabProps = {
  transactions: BillingTransaction[];
  loading: boolean;
  defaultFilters: BillingTransactionsParams;
  providers: BillingProvider[];
  contracts: BillingContract[];
  onApplyFilters: (params: BillingTransactionsParams) => Promise<void>;
  onRefresh: () => Promise<void>;
};

const DEFAULT_FILTER_STATE: TransactionFilterState = {
  status: 'all',
  provider: '',
  contract: '',
  network: '',
  dateFrom: '',
  dateTo: '',
  amountMin: '',
  amountMax: '',
};

export function TransactionsTab({
  transactions,
  loading,
  defaultFilters,
  providers,
  contracts,
  onApplyFilters,
  onRefresh,
}: TransactionsTabProps): React.ReactElement {
  const { pushToast } = useToast();
  const derivedDefaults = React.useMemo<TransactionFilterState>(() => {
    return {
      status: (defaultFilters.status as TransactionFilterState['status']) ?? 'all',
      provider: defaultFilters.provider ?? '',
      contract: defaultFilters.contract ?? '',
      network: defaultFilters.network ?? '',
      dateFrom: defaultFilters.from ?? '',
      dateTo: defaultFilters.to ?? '',
      amountMin:
        defaultFilters.min_amount != null
          ? String(defaultFilters.min_amount / 100)
          : '',
      amountMax:
        defaultFilters.max_amount != null
          ? String(defaultFilters.max_amount / 100)
          : '',
    };
  }, [defaultFilters]);

  const [filters, setFilters] = React.useState<TransactionFilterState>(derivedDefaults);
  const [page, setPage] = React.useState(1);
  const [detailsOpen, setDetailsOpen] = React.useState(false);
  const [selectedTx, setSelectedTx] = React.useState<BillingTransaction | null>(null);

  React.useEffect(() => {
    setFilters(derivedDefaults);
  }, [derivedDefaults]);

  React.useEffect(() => {
    setPage(1);
  }, [transactions]);

  const providerOptions = React.useMemo(
    () => providers.map((item) => item.slug).filter(Boolean).sort(),
    [providers],
  );

  const contractOptions = React.useMemo(
    () => contracts.map((item) => item.slug || item.id).filter(Boolean).sort(),
    [contracts],
  );

  const networkOptions = React.useMemo(
    () => getNetworkOptions(transactions),
    [transactions],
  );

  const pageData = React.useMemo(() => {
    const total = Math.max(1, Math.ceil(transactions.length / PAGE_SIZE));
    const current = Math.min(Math.max(1, page), total);
    const start = (current - 1) * PAGE_SIZE;
    return {
      total,
      page: current,
      items: transactions.slice(start, start + PAGE_SIZE),
    };
  }, [page, transactions]);

  const applyFilters = async () => {
    const params: BillingTransactionsParams = { limit: 200 };
    if (filters.status !== 'all') params.status = filters.status;
    if (filters.provider) params.provider = filters.provider.toLowerCase();
    if (filters.contract) params.contract = filters.contract.toLowerCase();
    if (filters.network) params.network = filters.network.toLowerCase();
    if (filters.dateFrom) params.from = filters.dateFrom;
    if (filters.dateTo) params.to = filters.dateTo;
    if (filters.amountMin)
      params.min_amount = Math.round(Number(filters.amountMin) * 100);
    if (filters.amountMax)
      params.max_amount = Math.round(Number(filters.amountMax) * 100);

    try {
      await onApplyFilters(params);
      setPage(1);
    } catch (err) {
      pushToast({
        intent: 'error',
        description:
          err instanceof Error ? err.message : 'Не удалось применить фильтры',
      });
    }
  };

  const resetFilters = async () => {
    setFilters(DEFAULT_FILTER_STATE);
    try {
      await onApplyFilters({ limit: 200 });
      setPage(1);
    } catch (err) {
      pushToast({
        intent: 'error',
        description:
          err instanceof Error ? err.message : 'Не удалось сбросить фильтры',
      });
    }
  };

  const openDetails = (tx: BillingTransaction) => {
    setSelectedTx(tx);
    setDetailsOpen(true);
  };

  return (
    <div className="space-y-6">
      <Card className="p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-900">Фильтры транзакций</h2>
          <div className="flex gap-2">
            <Button size="sm" variant="ghost" onClick={() => void resetFilters()}>
              Сбросить
            </Button>
            <Button size="sm" onClick={() => void applyFilters()}>
              Применить
            </Button>
          </div>
        </div>
        <div className="grid gap-3 lg:grid-cols-4">
          <Select
            label="Статус"
            value={filters.status}
            onChange={(event) =>
              setFilters((prev) => ({
                ...prev,
                status: event.target.value as TransactionFilterState['status'],
              }))
            }
          >
            <option value="all">Все</option>
            <option value="succeeded">Успешные</option>
            <option value="failed">Ошибки</option>
            <option value="pending">В ожидании</option>
          </Select>
          <Select
            label="Провайдер"
            value={filters.provider}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, provider: event.target.value }))
            }
          >
            <option value="">Все</option>
            {providerOptions.map((slug) => (
              <option key={slug} value={slug}>
                {slug}
              </option>
            ))}
          </Select>
          <Select
            label="Контракт"
            value={filters.contract}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, contract: event.target.value }))
            }
          >
            <option value="">Все</option>
            {contractOptions.map((slug) => (
              <option key={slug} value={slug}>
                {slug}
              </option>
            ))}
          </Select>
          <Select
            label="Сеть"
            value={filters.network}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, network: event.target.value }))
            }
          >
            <option value="">Все</option>
            {networkOptions.map((network) => (
              <option key={network} value={network}>
                {network}
              </option>
            ))}
          </Select>
          <Input
            label="Дата от"
            type="date"
            value={filters.dateFrom}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, dateFrom: event.target.value }))
            }
          />
          <Input
            label="Дата до"
            type="date"
            value={filters.dateTo}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, dateTo: event.target.value }))
            }
          />
          <Input
            label="Сумма от ($)"
            type="number"
            value={filters.amountMin}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, amountMin: event.target.value }))
            }
          />
          <Input
            label="Сумма до ($)"
            type="number"
            value={filters.amountMax}
            onChange={(event) =>
              setFilters((prev) => ({ ...prev, amountMax: event.target.value }))
            }
          />
        </div>
      </Card>

      <Card className="p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Транзакции</h2>
            <p className="text-sm text-gray-500">История платежей с учётом выбранных фильтров.</p>
          </div>
          <Button
            size="sm"
            variant="outlined"
            onClick={async () => {
              try {
                await onRefresh();
              } catch (err) {
                pushToast({
                  intent: 'error',
                  description:
                    err instanceof Error
                      ? err.message
                      : 'Не удалось обновить транзакции',
                });
              }
            }}
          >
            Обновить
          </Button>
        </div>

        <div className="relative">
          {loading ? (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/70">
              <Skeleton className="h-12 w-12 rounded-full" />
            </div>
          ) : null}
          <Table.Table className="min-w-[960px]">
            <Table.THead>
              <Table.TR>
                <Table.TH>Время</Table.TH>
                <Table.TH>Провайдер</Table.TH>
                <Table.TH>Пользователь</Table.TH>
                <Table.TH>Сеть</Table.TH>
                <Table.TH>Сумма (gross)</Table.TH>
                <Table.TH>Сумма (net)</Table.TH>
                <Table.TH>Статус</Table.TH>
                <Table.TH>Действия</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {pageData.items.map((tx, index) => {
                const status = getTxStatusMeta(tx.status);
                const rowKey = tx.tx_hash ?? `${tx.created_at ?? 'tx'}-${index}`;
                return (
                  <Table.TR key={rowKey}>
                    <Table.TD>{formatDate(tx.created_at)}</Table.TD>
                    <Table.TD>{tx.gateway_slug || '—'}</Table.TD>
                    <Table.TD className="font-mono text-xs">{tx.user_id || '—'}</Table.TD>
                    <Table.TD>{tx.network || '—'}</Table.TD>
                    <Table.TD>{centsToUsd(tx.gross_cents)}</Table.TD>
                    <Table.TD>{centsToUsd(tx.net_cents)}</Table.TD>
                    <Table.TD>
                      <Badge color={status.color}>{status.label}</Badge>
                    </Table.TD>
                    <Table.TD>
                      <Button
                        size="xs"
                        variant="ghost"
                        onClick={() => openDetails(tx)}
                      >
                        Подробнее
                      </Button>
                    </Table.TD>
                  </Table.TR>
                );
              })}
            </Table.TBody>
          </Table.Table>
        </div>

        <div className="mt-4 flex justify-end">
          <Pagination
            page={pageData.page}
            total={pageData.total}
            onChange={setPage}
          />
        </div>
      </Card>

      <Drawer
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        title="Детали транзакции"
        widthClass="w-[560px]"
      >
        {selectedTx ? (
          <div className="space-y-3 px-4 py-5 text-sm">
            <div className="grid gap-2">
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Статус</span>
                <Badge color={getTxStatusMeta(selectedTx.status).color}>
                  {getTxStatusMeta(selectedTx.status).label}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Провайдер</span>
                <span className="font-mono text-xs">{selectedTx.gateway_slug || '—'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Пользователь</span>
                <span className="font-mono text-xs">{selectedTx.user_id || '—'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Сеть</span>
                <span>{selectedTx.network || '—'}</span>
              </div>
            </div>
            <div className="grid gap-2">
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Сумма (gross)</span>
                <span className="font-semibold text-gray-900">{centsToUsd(selectedTx.gross_cents)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Сумма (net)</span>
                <span>{centsToUsd(selectedTx.net_cents)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Fee</span>
                <span>{centsToUsd(selectedTx.fee_cents)}</span>
              </div>
            </div>
            <div className="grid gap-2">
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Создана</span>
                <span>{formatDate(selectedTx.created_at)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Подтверждена</span>
                <span>{formatDate(selectedTx.confirmed_at)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Tx hash</span>
                {selectedTx.tx_hash ? (
                  <a
                    className="text-primary-600 hover:underline"
                    href={txExplorerUrl(selectedTx.network, selectedTx.tx_hash) || '#'}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {selectedTx.tx_hash.slice(0, 12)}…
                  </a>
                ) : (
                  <span>—</span>
                )}
              </div>
            </div>
            {selectedTx.failure_reason ? (
              <Card className="border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
                Причина отказа: {selectedTx.failure_reason}
              </Card>
            ) : null}
            <Card className="bg-gray-50 p-3 text-xs">
              <div className="font-semibold text-gray-700">Meta payload</div>
              <pre className="mt-2 max-h-48 overflow-auto rounded bg-white/70 p-3">
                {JSON.stringify(selectedTx.meta ?? {}, null, 2)}
              </pre>
            </Card>
          </div>
        ) : null}
      </Drawer>
    </div>
  );
}
