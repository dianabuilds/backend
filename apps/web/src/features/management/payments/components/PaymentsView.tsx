import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { Button, Card, Tabs, useToast } from '@ui';

import { useManagementPayments } from '../hooks';
import { fetchBillingCryptoConfig } from '@shared/api/management';

import { ProvidersTab } from './tabs/ProvidersTab';
import { ContractsTab } from './tabs/ContractsTab';
import { TransactionsTab } from './tabs/TransactionsTab';
import { CryptoTab } from './tabs/CryptoTab';

import type { BillingTransactionsParams } from '@shared/api/management/billing';
import type { BillingCryptoConfig } from '@shared/types/management';

const TAB_PARAM = 'tab';

type TabKey = 'providers' | 'contracts' | 'transactions' | 'crypto';

export default function ManagementPayments(): React.ReactElement {
  const {
    loading,
    error: dataError,
    clearError: clearDataError,
    refresh,
    kpi,
    providers,
    transactions,
    transactionsLoading,
    transactionFilters,
    loadTransactions,
    contracts,
    contractEvents,
    loadContractEvents,
    cryptoConfig,
    updateCryptoConfig,
    saveProvider,
    deleteProvider,
    saveContract,
    deleteContract,
  } = useManagementPayments();
  const { pushToast } = useToast();

  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = (searchParams.get(TAB_PARAM) as TabKey) ?? 'providers';
  const [activeTab, setActiveTab] = React.useState<TabKey>(initialTab);

  React.useEffect(() => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set(TAB_PARAM, activeTab);
      return next;
    });
  }, [activeTab, setSearchParams]);

  React.useEffect(() => {
    if (!dataError) return;
    pushToast({ intent: 'error', description: dataError });
    clearDataError();
  }, [clearDataError, dataError, pushToast]);

  const handleApplyTransactions = React.useCallback(
    (params: BillingTransactionsParams) => loadTransactions(params),
    [loadTransactions],
  );

  const handleRefreshTransactions = React.useCallback(
    () => loadTransactions(transactionFilters),
    [loadTransactions, transactionFilters],
  );

  const handleSaveCrypto = React.useCallback(
    (payload: BillingCryptoConfig) => updateCryptoConfig(payload),
    [updateCryptoConfig],
  );

  const handleTestCrypto = React.useCallback(async () => {
    await fetchBillingCryptoConfig();
  }, []);

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Payments workspace</h1>
          <p className="text-sm text-gray-500">
            Управление шлюзами, контрактами и мониторинг транзакций в едином интерфейсе.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outlined"
            onClick={() => void handleRefreshTransactions()}
          >
            Обновить транзакции
          </Button>
          <Button size="sm" onClick={() => void refresh()}>
            Обновить всё
          </Button>
        </div>
      </div>

      <Tabs
        items={[
          { key: 'providers', label: 'Провайдеры' },
          { key: 'contracts', label: 'Контракты' },
          { key: 'transactions', label: 'Транзакции' },
          { key: 'crypto', label: 'Крипто' },
        ]}
        value={activeTab}
        onChange={(key) => setActiveTab(key as TabKey)}
      />

      {activeTab === 'providers' ? (
        <ProvidersTab
          loading={loading}
          kpi={kpi}
          providers={providers}
          contracts={contracts}
          onSave={saveProvider}
          onDelete={deleteProvider}
        />
      ) : null}

      {activeTab === 'contracts' ? (
        <ContractsTab
          contracts={contracts}
          contractEvents={contractEvents}
          onSave={saveContract}
          onDelete={deleteContract}
          onLoadEvents={loadContractEvents}
        />
      ) : null}

      {activeTab === 'transactions' ? (
        <TransactionsTab
          transactions={transactions}
          loading={transactionsLoading}
          defaultFilters={transactionFilters}
          providers={providers}
          contracts={contracts}
          onApplyFilters={handleApplyTransactions}
          onRefresh={handleRefreshTransactions}
        />
      ) : null}

      {activeTab === 'crypto' ? (
        <CryptoTab
          config={cryptoConfig}
          onSave={handleSaveCrypto}
          onTest={handleTestCrypto}
        />
      ) : null}

      <Card className="border border-transparent">
        <div className="text-xs text-gray-400">
          Последнее обновление: {new Date().toLocaleString()}
        </div>
      </Card>
    </div>
  );
}
