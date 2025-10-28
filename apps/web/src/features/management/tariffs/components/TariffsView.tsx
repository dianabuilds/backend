import React from 'react';
import { Users, Coins, Gauge, TrendingDown, FlaskConical } from '@icons';
import { Button, Card, Tabs } from '@ui';

import { extractErrorMessage } from '@shared/utils/errors';
import { useManagementTariffs } from '../hooks';
import type {
  BillingPlan,
  BillingPlanHistoryItem,
  BillingPlanLimitsUpdate,
} from '@shared/types/management';

import {
  createFormFromPlan,
  DEFAULT_PLAN_FORM,
  PlanFormState,
  buildPlanPayload,
  countExperiments,
} from './helpers';
import { PlansCatalog, PlanFilters } from './PlansCatalog';
import { PlanEditorDrawer } from './PlanEditorDrawer';
import { LimitsMatrix } from './LimitsMatrix';

type MatrixTabKey = 'catalog' | 'matrix' | 'history';

const DEFAULT_FILTERS: PlanFilters = {
  search: '',
  status: 'all',
  interval: 'all',
  token: '',
};

export default function TariffsView(): React.ReactElement {
  const {
    loading,
    error,
    metrics,
    plans,
    history,
    refresh,
    clearError,
    savePlan,
    deletePlan,
    updatePlanLimits,
    loadPlanHistory,
  } = useManagementTariffs();

  const [filters, setFilters] = React.useState<PlanFilters>(DEFAULT_FILTERS);
  const [activeTab, setActiveTab] = React.useState<MatrixTabKey>('catalog');
  const [editorOpen, setEditorOpen] = React.useState(false);
  const [editorSaving, setEditorSaving] = React.useState(false);
  const [editorError, setEditorError] = React.useState<string | null>(null);
  const [editorForm, setEditorForm] = React.useState<PlanFormState>(DEFAULT_PLAN_FORM);
  const [editorPlan, setEditorPlan] = React.useState<BillingPlan | null>(null);
  const [editorInitialTab, setEditorInitialTab] = React.useState<'general' | 'history'>('general');
  const [historyLoading, setHistoryLoading] = React.useState(false);
  const [editorHistory, setEditorHistory] = React.useState<BillingPlanHistoryItem[]>([]);

  React.useEffect(() => {
    if (!editorPlan) return;
    const matched = history.filter(
      (item) =>
        item.resource_id === editorPlan.slug || item.resource_id === editorPlan.id,
    );
    setEditorHistory(matched);
  }, [history, editorPlan]);

  const experiments = React.useMemo(() => countExperiments(plans), [plans]);

  React.useEffect(() => {
    if (activeTab === 'history' && plans.length) {
      void loadPlanHistory(plans[0].slug);
    }
  }, [activeTab, loadPlanHistory, plans]);

  const handleCreate = () => {
    setEditorForm({ ...DEFAULT_PLAN_FORM });
    setEditorPlan(null);
    setEditorInitialTab('general');
    setEditorError(null);
    setEditorHistory([]);
    setEditorOpen(true);
  };

  const handleEdit = (plan: BillingPlan) => {
    setEditorForm(createFormFromPlan(plan));
    setEditorPlan(plan);
    setEditorInitialTab('general');
    setEditorError(null);
     setEditorHistory([]);
    setEditorOpen(true);
  };

  const handleHistory = async (plan: BillingPlan) => {
    setEditorForm(createFormFromPlan(plan));
    setEditorPlan(plan);
    setEditorInitialTab('history');
    setEditorError(null);
    setEditorHistory([]);
    setEditorOpen(true);
    setHistoryLoading(true);
    try {
      await loadPlanHistory(plan.slug);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleSave = async () => {
    const payload = buildPlanPayload(editorForm);
    if (!payload) {
      setEditorError('Slug обязателен.');
      return;
    }
    setEditorSaving(true);
    setEditorError(null);
    try {
      await savePlan(payload);
      setEditorOpen(false);
    } catch (err) {
      setEditorError(extractErrorMessage(err, 'Не удалось сохранить тариф.'));
    } finally {
      setEditorSaving(false);
    }
  };

  const handleDelete = async (plan: BillingPlan) => {
    if (!plan.id) return;
    const confirmed = window.confirm(`Удалить тариф «${plan.title || plan.slug}»?`);
    if (!confirmed) return;
    await deletePlan(plan.id);
  };

  const handleSaveMatrix = async (updates: BillingPlanLimitsUpdate[]) => {
    await updatePlanLimits(updates);
  };

  const kpiCards = [
    {
      icon: <Users className="h-5 w-5" />,
      label: 'Активные подписчики',
      value: metrics.active_subs.toLocaleString(),
    },
    {
      icon: <Coins className="h-5 w-5" />,
      label: 'MRR',
      value: `$${(metrics.mrr ?? 0).toFixed(2)}`,
    },
    {
      icon: <Gauge className="h-5 w-5" />,
      label: 'ARPU',
      value: `$${(metrics.arpu ?? 0).toFixed(2)}`,
    },
    {
      icon: <TrendingDown className="h-5 w-5" />,
      label: 'Churn 30d',
      value: `${(metrics.churn_30d ?? 0).toFixed(2)}%`,
    },
    {
      icon: <FlaskConical className="h-5 w-5" />,
      label: 'Эксперименты',
      value: `${experiments.activeExperiments}/${experiments.experiments}`,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Tariff plans</h1>
          <p className="text-sm text-gray-500">
            Управляйте тарифами, экспериментами и лимитами в едином рабочем пространстве.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outlined" onClick={() => clearError()}>
            Скрыть ошибки
          </Button>
          <Button size="sm" onClick={() => void refresh()}>
            Обновить данные
          </Button>
        </div>
      </div>

      {error ? (
        <Card className="border border-rose-200 bg-rose-50 p-4 text-sm text-rose-600">
          {error}
        </Card>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {kpiCards.map((card, index) => (
          <Card key={card.label + index} className="flex items-center gap-3 border border-gray-100 p-4 shadow-sm">
            <div className="rounded-full bg-gray-100 p-2 text-gray-600">
              {card.icon}
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-gray-500">{card.label}</div>
              <div className="text-lg font-semibold text-gray-900">{card.value}</div>
            </div>
          </Card>
        ))}
      </div>

      <Tabs
        items={[
          { key: 'catalog', label: 'Каталог' },
          { key: 'matrix', label: 'Лимиты' },
          { key: 'history', label: 'История' },
        ]}
        value={activeTab}
        onChange={(key) => setActiveTab(key as MatrixTabKey)}
      />

      {activeTab === 'catalog' ? (
      <PlansCatalog
        plans={plans}
        filters={filters}
        onChangeFilters={setFilters}
        onCreate={handleCreate}
        onEdit={handleEdit}
        onHistory={handleHistory}
        onDelete={handleDelete}
      />
      ) : null}

      {activeTab === 'matrix' ? (
        <LimitsMatrix plans={plans} saving={loading} onSave={handleSaveMatrix} />
      ) : null}

      {activeTab === 'history' ? (
        <Card className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">
              История операций
            </h2>
            <Button size="sm" onClick={() => void refresh()}>
              Обновить
            </Button>
          </div>
          {history.length === 0 ? (
            <div className="text-sm text-gray-500">История изменений тарифов отсутствует.</div>
          ) : (
            <div className="space-y-3">
              {history.map((item) => (
                <Card key={item.id || `${item.action}-${item.created_at}`} className="border border-gray-200 p-3 text-xs">
                  <div className="flex items-center justify-between">
                    <div className="font-semibold text-gray-700">{item.action || 'update'}</div>
                    <div className="text-gray-500">{item.actor || '—'}</div>
                  </div>
                  <div className="mt-1 text-gray-500">
                    {item.created_at ? new Date(item.created_at).toLocaleString() : '—'}
                  </div>
                  <pre className="mt-2 max-h-40 overflow-auto rounded bg-gray-50 p-2">
                    {JSON.stringify(item.payload || {}, null, 2)}
                  </pre>
                </Card>
              ))}
            </div>
          )}
        </Card>
      ) : null}

      <PlanEditorDrawer
        open={editorOpen}
        saving={editorSaving}
        form={editorForm}
        error={editorError}
        history={editorHistory}
        historyLoading={historyLoading}
        onClose={() => setEditorOpen(false)}
        onChange={(updater) => setEditorForm(updater)}
        onSave={handleSave}
        onLoadHistory={async () => {
          if (!editorPlan) return;
          setHistoryLoading(true);
          try {
            await loadPlanHistory(editorPlan.slug);
          } finally {
            setHistoryLoading(false);
          }
        }}
        initialTab={editorInitialTab}
      />
    </div>
  );
}
