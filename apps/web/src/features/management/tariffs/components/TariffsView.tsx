import React from 'react';
import { Users, Coins, Gauge, TrendingDown } from '@icons';
import { Badge, Button, Card, Drawer, Input, Select, Spinner, Table, Tabs, Textarea } from '@ui';
import { extractErrorMessage } from '@shared/utils/errors';
import { useManagementTariffs } from '../hooks';
import type {
  BillingPlan,
  BillingPlanLimitsUpdate,
  BillingPlanPayload,
} from '@shared/types/management';

type TabKey = 'plans' | 'matrix' | 'history';

type PlanFormFeatures = {
  status: string;
  audience: string;
  trial_days: string;
  ab_variant: string;
  flags: string;
  models_allowed: string;
  ai_quest_generator: boolean;
  compass_enhanced: boolean;
  progress_map: boolean;
  history_advanced: boolean;
  exclusive_caves: boolean;
  achievements: boolean;
};

type BooleanFeatureKey =
  | 'ai_quest_generator'
  | 'compass_enhanced'
  | 'progress_map'
  | 'history_advanced'
  | 'exclusive_caves'
  | 'achievements';

type PlanFormState = {
  id?: string;
  slug: string;
  title: string;
  description: string;
  price_cents: string;
  currency: string;
  is_active: boolean;
  order: string;
  monthly_limits: Record<string, string>;
  features: PlanFormFeatures;
};

const LIMIT_KEYS: Array<{ key: string; label: string }> = [
  { key: 'llm_tokens_month', label: 'LLM tokens / month' },
  { key: 'quest_generations', label: 'Quest generations' },
  { key: 'echo_traces', label: 'Echo traces' },
  { key: 'tag_notifications', label: 'Tag notifications' },
  { key: 'worlds_max', label: 'Worlds max' },
  { key: 'nodes_max', label: 'Nodes max' },
  { key: 'transitions_max', label: 'Transitions max' },
  { key: 'api_quota', label: 'API quota' },
];

const BOOL_FEATURE_KEYS: Array<{ key: BooleanFeatureKey; label: string }> = [
  { key: 'ai_quest_generator', label: 'AI quest generator' },
  { key: 'compass_enhanced', label: 'Enhanced compass' },
  { key: 'progress_map', label: 'Progress map' },
  { key: 'history_advanced', label: 'Advanced history' },
  { key: 'exclusive_caves', label: 'Exclusive caves' },
  { key: 'achievements', label: 'Achievements' },
];

const DEFAULT_FEATURES: PlanFormFeatures = {
  status: 'draft',
  audience: 'off',
  trial_days: '',
  ab_variant: 'control',
  flags: '',
  models_allowed: '',
  ai_quest_generator: false,
  compass_enhanced: false,
  progress_map: false,
  history_advanced: false,
  exclusive_caves: false,
  achievements: false,
};

const DEFAULT_PLAN_FORM: PlanFormState = {
  slug: '',
  title: '',
  description: '',
  price_cents: '',
  currency: 'USD',
  is_active: false,
  order: '',
  monthly_limits: LIMIT_KEYS.reduce<Record<string, string>>((acc, item) => {
    acc[item.key] = '';
    return acc;
  }, {}),
  features: { ...DEFAULT_FEATURES },
};

function createFormFromPlan(plan: BillingPlan): PlanFormState {
  const limits = plan.monthly_limits && typeof plan.monthly_limits === 'object' ? plan.monthly_limits : {};
  const features = plan.features && typeof plan.features === 'object' ? plan.features : {};
  return {
    id: plan.id,
    slug: plan.slug,
    title: plan.title ?? '',
    description: plan.description ?? '',
    price_cents: plan.price_cents != null ? String(plan.price_cents) : '',
    currency: plan.currency ?? 'USD',
    is_active: Boolean(plan.is_active),
    order: plan.order != null ? String(plan.order) : '',
    monthly_limits: LIMIT_KEYS.reduce<Record<string, string>>((acc, item) => {
      const value = limits[item.key];
      acc[item.key] = value != null ? String(value) : '';
      return acc;
    }, {}),
    features: {
      status: String(features.status ?? (plan.is_active ? 'active' : 'draft')),
      audience: String(features.audience ?? 'off'),
      trial_days: features.trial_days != null ? String(features.trial_days) : '',
      ab_variant: String(features.ab_variant ?? 'control'),
      flags: Array.isArray(features.flags)
        ? (features.flags as string[]).join(', ')
        : String(features.flags ?? ''),
      models_allowed: Array.isArray(features.models_allowed)
        ? (features.models_allowed as string[]).join(', ')
        : String(features.models_allowed ?? ''),
      ai_quest_generator: Boolean(features.ai_quest_generator),
      compass_enhanced: Boolean(features.compass_enhanced),
      progress_map: Boolean(features.progress_map),
      history_advanced: Boolean(features.history_advanced),
      exclusive_caves: Boolean(features.exclusive_caves),
      achievements: Boolean(features.achievements),
    },
  };
}

function formatCurrency(cents?: number | null, currency = 'USD'): string {
  if (cents == null || Number.isNaN(cents)) return '—';
  const amount = (cents / 100).toFixed(2);
  return `${currency} ${amount}`;
}

function formatNumber(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return '—';
  return value.toLocaleString();
}

function parseNumber(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number(trimmed);
  return Number.isNaN(parsed) ? null : parsed;
}

function parseIntOrNull(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = parseInt(trimmed, 10);
  return Number.isNaN(parsed) ? null : parsed;
}

export default function ManagementTariffs(): React.ReactElement {
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

  const [activeTab, setActiveTab] = React.useState<TabKey>('plans');
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [form, setForm] = React.useState<PlanFormState>({ ...DEFAULT_PLAN_FORM });
  const [formError, setFormError] = React.useState<string | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [historyPlan, setHistoryPlan] = React.useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = React.useState(false);

  const [matrixDraft, setMatrixDraft] = React.useState<Record<string, Record<string, string>>>({});
  const [matrixSaving, setMatrixSaving] = React.useState(false);

  React.useEffect(() => {
    const draft: Record<string, Record<string, string>> = {};
    plans.forEach((plan) => {
      draft[plan.slug] = LIMIT_KEYS.reduce<Record<string, string>>((acc, item) => {
        const source = plan.monthly_limits && typeof plan.monthly_limits === 'object' ? plan.monthly_limits : {};
        const value = source[item.key];
        acc[item.key] = value != null ? String(value) : '';
        return acc;
      }, {});
    });
    setMatrixDraft(draft);
  }, [plans]);

  const handleOpenCreate = React.useCallback(() => {
    setForm({ ...DEFAULT_PLAN_FORM });
    setFormError(null);
    setDrawerOpen(true);
  }, []);

  const handleOpenEdit = React.useCallback((plan: BillingPlan) => {
    setForm(createFormFromPlan(plan));
    setFormError(null);
    setDrawerOpen(true);
  }, []);

  const handleCloseDrawer = React.useCallback(() => {
    setDrawerOpen(false);
    setForm({ ...DEFAULT_PLAN_FORM });
    setFormError(null);
  }, []);

  const buildPayload = React.useCallback((): BillingPlanPayload | null => {
    const slug = form.slug.trim();
    if (!slug) {
      setFormError('Slug is required.');
      return null;
    }
    const price = parseNumber(form.price_cents);
    const order = parseIntOrNull(form.order);

    const monthly_limits: Record<string, unknown> = {};
    Object.entries(form.monthly_limits).forEach(([key, value]) => {
      const parsed = parseIntOrNull(value);
      if (parsed != null) {
        monthly_limits[key] = parsed;
      }
    });

    const features: Record<string, unknown> = {
      status: form.features.status || 'draft',
      audience: form.features.audience || 'off',
    };

    const trial = parseIntOrNull(form.features.trial_days);
    if (trial != null) features.trial_days = trial;

    features.ab_variant = form.features.ab_variant || 'control';

    const flags = form.features.flags
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
    if (flags.length) features.flags = flags;

    const models = form.features.models_allowed
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
    if (models.length) features.models_allowed = models;

    BOOL_FEATURE_KEYS.forEach(({ key }) => {
      features[key] = form.features[key];
    });

    const payload: BillingPlanPayload = {
      id: form.id,
      slug,
      title: form.title.trim() || undefined,
      description: form.description.trim() || undefined,
      currency: form.currency.trim() || undefined,
      price_cents: price ?? null,
      is_active: form.is_active,
      order: order ?? undefined,
      monthly_limits: Object.keys(monthly_limits).length ? monthly_limits : null,
      features: Object.keys(features).length ? features : null,
    };

    return payload;
  }, [form]);

  const handleSavePlan = React.useCallback(async () => {
    const payload = buildPayload();
    if (!payload) return;
    setSaving(true);
    setFormError(null);
    try {
      await savePlan(payload);
      setDrawerOpen(false);
    } catch (err) {
      setFormError(extractErrorMessage(err, 'Не удалось сохранить тариф.'));
    } finally {
      setSaving(false);
    }
  }, [buildPayload, savePlan]);

  const handleDeletePlan = React.useCallback(async (plan: BillingPlan) => {
    if (!plan.id) return;
    const confirmed = window.confirm(`Удалить тариф «${plan.title || plan.slug}»?`);
    if (!confirmed) return;
    try {
      await deletePlan(plan.id);
    } catch (err) {
      console.error(err);
    }
  }, [deletePlan]);

  const handleSaveMatrix = React.useCallback(async () => {
    const updates: BillingPlanLimitsUpdate[] = Object.entries(matrixDraft).map(([slug, limits]) => {
      const sanitized: Record<string, unknown> = {};
      Object.entries(limits).forEach(([key, value]) => {
        const parsed = parseIntOrNull(value);
        if (parsed != null) {
          sanitized[key] = parsed;
        }
      });
      return { slug, monthly_limits: sanitized };
    });
    setMatrixSaving(true);
    try {
      await updatePlanLimits(updates);
    } catch (err) {
      console.error(err);
    } finally {
      setMatrixSaving(false);
    }
  }, [matrixDraft, updatePlanLimits]);

  const handleShowHistory = React.useCallback(
    async (plan: BillingPlan) => {
      setHistoryPlan(plan.slug);
      setActiveTab('history');
      setHistoryLoading(true);
      try {
        await loadPlanHistory(plan.slug);
      } catch (err) {
        console.error(err);
      } finally {
        setHistoryLoading(false);
      }
    },
    [loadPlanHistory],
  );

  const handleRefresh = React.useCallback(() => {
    clearError();
    void refresh();
  }, [clearError, refresh]);

  const plansEmpty = plans.length === 0;
  const historyAvailable = Boolean(historyPlan) || history.length > 0;
  const tabsItems = React.useMemo(
    () => [
      { key: 'plans', label: 'Plans' },
      { key: 'matrix', label: 'Limits matrix' },
      {
        key: 'history',
        label: (
          <span className={historyAvailable ? '' : 'text-gray-400'}>
            History
          </span>
        ),
      },
    ],
    [historyAvailable],
  );

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={<Users className="h-5 w-5" />} label="Active subscribers" value={formatNumber(metrics.active_subs)} />
        <MetricCard icon={<Coins className="h-5 w-5" />} label="MRR" value={`$${(metrics.mrr ?? 0).toFixed(2)}`} />
        <MetricCard icon={<Gauge className="h-5 w-5" />} label="ARPU" value={`$${(metrics.arpu ?? 0).toFixed(2)}`} />
        <MetricCard icon={<TrendingDown className="h-5 w-5" />} label="Churn 30d" value={`${(metrics.churn_30d ?? 0).toFixed(2)}%`} />
      </div>

      <Card className="space-y-4 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-gray-900 dark:text-white">Tariff plans</h2>
            <p className="text-sm text-gray-500 dark:text-dark-200">Manage product tiers, limits, and experiments.</p>
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" color="primary" onClick={handleOpenCreate}>
              Create plan
            </Button>
            <Button size="sm" variant="outlined" onClick={handleRefresh} disabled={loading}>
              Refresh
            </Button>
          </div>
        </div>

        {error ? (
          <div className="flex items-start justify-between gap-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-400/30 dark:bg-rose-500/10 dark:text-rose-200">
            <span>{error}</span>
            <Button size="xs" variant="ghost" onClick={clearError}>
              Скрыть
            </Button>
          </div>
        ) : null}

        <Tabs
          items={tabsItems}
          value={activeTab}
          onChange={(key) => {
            if (key === 'history' && !historyAvailable) return;
            setActiveTab(key as TabKey);
          }}
        />

        {activeTab === 'plans' ? (
          loading && plansEmpty ? (
            <div className="flex min-h-[160px] items-center justify-center">
              <Spinner />
            </div>
          ) : plansEmpty ? (
            <div className="rounded-xl border border-dashed border-gray-200 px-6 py-10 text-center text-sm text-gray-500 dark:border-dark-600 dark:text-dark-200">
              No plans yet. Create the first tariff to unlock billing features.
            </div>
          ) : (
            <div className="-mx-4 overflow-x-auto sm:mx-0">
              <Table.Table className="min-w-[720px] text-left text-sm">
                <Table.THead>
                  <Table.TR>
                    <Table.TH className="px-4 py-3">Plan</Table.TH>
                    <Table.TH className="px-4 py-3">Price</Table.TH>
                    <Table.TH className="px-4 py-3">Features</Table.TH>
                    <Table.TH className="px-4 py-3">Updated</Table.TH>
                    <Table.TH className="px-4 py-3 text-right">Actions</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {plans.map((plan) => (
                    <Table.TR key={plan.id} className="border-b border-gray-100 last:border-none dark:border-dark-600">
                      <Table.TD className="px-4 py-3 align-top">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-gray-900 dark:text-white">{plan.title || plan.slug}</span>
                            <Badge variant="soft" color={plan.is_active ? 'success' : 'neutral'}>
                              {plan.is_active ? 'Active' : 'Hidden'}
                            </Badge>
                          </div>
                          <div className="text-xs text-gray-500 dark:text-dark-200">{plan.description || '—'}</div>
                        </div>
                      </Table.TD>
                      <Table.TD className="px-4 py-3 align-top">{formatCurrency(plan.price_cents, plan.currency ?? 'USD')}</Table.TD>
                      <Table.TD className="px-4 py-3 align-top">
                        <div className="space-y-1 text-xs text-gray-600 dark:text-dark-200">
                          <div>Audience: {String(plan.features?.audience ?? 'off')}</div>
                          <div>Status: {String(plan.features?.status ?? (plan.is_active ? 'active' : 'draft'))}</div>
                          {plan.monthly_limits ? (
                            <div>
                              Limits:{' '}
                              {LIMIT_KEYS.filter((item) => plan.monthly_limits?.[item.key] != null)
                                .map((item) => `${item.key}=${plan.monthly_limits?.[item.key]}`)
                                .join(', ') || '—'}
                            </div>
                          ) : null}
                        </div>
                      </Table.TD>
                      <Table.TD className="px-4 py-3 align-top text-xs text-gray-500 dark:text-dark-200">
                        {plan.updated_at ? new Date(plan.updated_at).toLocaleString() : '—'}
                      </Table.TD>
                      <Table.TD className="px-4 py-3 text-right align-top">
                        <div className="inline-flex items-center gap-2">
                          <Button size="xs" variant="ghost" onClick={() => handleOpenEdit(plan)}>
                            Edit
                          </Button>
                          <Button size="xs" variant="ghost" onClick={() => handleShowHistory(plan)}>
                            History
                          </Button>
                          <Button size="xs" variant="ghost" color="error" onClick={() => void handleDeletePlan(plan)}>
                            Delete
                          </Button>
                        </div>
                      </Table.TD>
                    </Table.TR>
                  ))}
                </Table.TBody>
              </Table.Table>
            </div>
          )
        ) : null}

        {activeTab === 'matrix' ? (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-dark-200">
              Update monthly limits across plans in one go. Leave fields empty to keep current values.
            </p>
            <div className="-mx-4 overflow-x-auto sm:mx-0">
              <Table.Table className="min-w-[720px] text-left text-sm">
                <Table.THead>
                  <Table.TR>
                    <Table.TH className="px-4 py-3">Plan</Table.TH>
                    {LIMIT_KEYS.map((item) => (
                      <Table.TH key={item.key} className="px-4 py-3 text-right">
                        {item.label}
                      </Table.TH>
                    ))}
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {plans.map((plan) => (
                    <Table.TR key={`matrix-${plan.slug}`} className="border-b border-gray-100 last:border-none dark:border-dark-600">
                      <Table.TD className="px-4 py-3 font-medium text-gray-900 dark:text-white">{plan.title || plan.slug}</Table.TD>
                      {LIMIT_KEYS.map((item) => (
                        <Table.TD key={item.key} className="px-4 py-3 text-right">
                          <Input
                            value={matrixDraft[plan.slug]?.[item.key] ?? ''}
                            onChange={(event) =>
                              setMatrixDraft((prev) => ({
                                ...prev,
                                [plan.slug]: {
                                  ...(prev[plan.slug] || {}),
                                  [item.key]: event.target.value,
                                },
                              }))
                            }
                            className="w-24 text-right"
                          />
                        </Table.TD>
                      ))}
                    </Table.TR>
                  ))}
                </Table.TBody>
              </Table.Table>
            </div>
            <div className="flex justify-end">
              <Button onClick={() => void handleSaveMatrix()} disabled={matrixSaving}>
                {matrixSaving ? 'Saving…' : 'Save limits'}
              </Button>
            </div>
          </div>
        ) : null}

        {activeTab === 'history' ? (
          historyLoading ? (
            <div className="flex min-h-[120px] items-center justify-center">
              <Spinner />
            </div>
          ) : history.length === 0 ? (
            <div className="rounded-xl border border-dashed border-gray-200 px-6 py-10 text-center text-sm text-gray-500 dark:border-dark-600 dark:text-dark-200">
              No history records yet. Select a plan to inspect changes.
            </div>
          ) : (
            <div className="space-y-3">
              <div className="text-sm text-gray-500 dark:text-dark-200">History for: {historyPlan ?? 'selected plan'}</div>
              <div className="rounded-xl border border-gray-200 dark:border-dark-600">
                <Table.Table className="w-full text-left text-sm">
                  <Table.THead>
                    <Table.TR>
                      <Table.TH className="px-4 py-3">Action</Table.TH>
                      <Table.TH className="px-4 py-3">Actor</Table.TH>
                      <Table.TH className="px-4 py-3">Timestamp</Table.TH>
                      <Table.TH className="px-4 py-3">Payload</Table.TH>
                    </Table.TR>
                  </Table.THead>
                  <Table.TBody>
                    {history.map((item) => (
                      <Table.TR key={item.id ?? `${item.action}-${item.created_at}`}
                        className="border-b border-gray-100 last:border-none dark:border-dark-600">
                        <Table.TD className="px-4 py-3 align-top font-medium text-gray-900 dark:text-white">
                          {item.action || 'update'}
                        </Table.TD>
                        <Table.TD className="px-4 py-3 align-top text-xs text-gray-500 dark:text-dark-200">
                          {item.actor || '—'}
                        </Table.TD>
                        <Table.TD className="px-4 py-3 align-top text-xs text-gray-500 dark:text-dark-200">
                          {item.created_at ? new Date(item.created_at).toLocaleString() : '—'}
                        </Table.TD>
                        <Table.TD className="px-4 py-3 align-top">
                          <Textarea readOnly value={JSON.stringify(item.payload ?? {}, null, 2)} className="h-32 text-xs" />
                        </Table.TD>
                      </Table.TR>
                    ))}
                  </Table.TBody>
                </Table.Table>
              </div>
            </div>
          )
        ) : null}
      </Card>

      <Drawer
        open={drawerOpen}
        onClose={handleCloseDrawer}
        title={form.id ? 'Edit plan' : 'Create plan'}
        widthClass="w-[540px]"
        footer={(
          <div className="flex items-center justify-between gap-2">
            {formError ? <span className="text-sm text-rose-500">{formError}</span> : <span />}
            <div className="flex items-center gap-2">
              <Button variant="ghost" onClick={handleCloseDrawer}>
                Cancel
              </Button>
              <Button onClick={() => void handleSavePlan()} disabled={saving}>
                {saving ? 'Saving…' : form.id ? 'Save changes' : 'Create plan'}
              </Button>
            </div>
          </div>
        )}
      >
        <div className="space-y-4 px-4 py-5">
          <Input
            label="Slug"
            value={form.slug}
            onChange={(event) => setForm((prev) => ({ ...prev, slug: event.target.value }))}
            disabled={Boolean(form.id)}
            required
          />
          <Input
            label="Title"
            value={form.title}
            onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
          />
          <Textarea
            label="Description"
            value={form.description}
            onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
            rows={3}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Price (cents)"
              value={form.price_cents}
              onChange={(event) => setForm((prev) => ({ ...prev, price_cents: event.target.value }))}
            />
            <Input
              label="Currency"
              value={form.currency}
              onChange={(event) => setForm((prev) => ({ ...prev, currency: event.target.value }))}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Order"
              value={form.order}
              onChange={(event) => setForm((prev) => ({ ...prev, order: event.target.value }))}
            />
            <Select
              label="Status"
              value={form.features.status}
              onChange={(event) => {
                const value = event.target.value;
                setForm((prev) => ({
                  ...prev,
                  is_active: value === 'active',
                  features: { ...prev.features, status: value },
                }));
              }}
            >
              <option value="active">active</option>
              <option value="hidden">hidden</option>
              <option value="draft">draft</option>
              <option value="archived">archived</option>
            </Select>
          </div>
          <Select
            label="Audience"
            value={form.features.audience}
            onChange={(event) =>
              setForm((prev) => ({
                ...prev,
                features: { ...prev.features, audience: event.target.value },
              }))
            }
          >
            <option value="off">Off</option>
            <option value="all">All</option>
            <option value="premium">Premium</option>
          </Select>

          <div className="space-y-2">
            <div className="text-sm font-semibold text-gray-900 dark:text-white">Monthly limits</div>
            {LIMIT_KEYS.map((item) => (
              <Input
                key={item.key}
                label={item.label}
                value={form.monthly_limits[item.key] ?? ''}
                onChange={(event) =>
                  setForm((prev) => ({
                    ...prev,
                    monthly_limits: { ...prev.monthly_limits, [item.key]: event.target.value },
                  }))
                }
              />
            ))}
          </div>

          <div className="space-y-2">
            <div className="text-sm font-semibold text-gray-900 dark:text-white">Feature flags</div>
            <Textarea
              label="Feature flags"
              placeholder="flag.alpha, flag.beta"
              value={form.features.flags}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, features: { ...prev.features, flags: event.target.value } }))
              }
            />
            <Textarea
              label="Allowed models"
              placeholder="gpt-4, llama-3"
              value={form.features.models_allowed}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, features: { ...prev.features, models_allowed: event.target.value } }))
              }
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Trial days"
              value={form.features.trial_days}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, features: { ...prev.features, trial_days: event.target.value } }))
              }
            />
            <Select
              label="AB variant"
              value={form.features.ab_variant}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, features: { ...prev.features, ab_variant: event.target.value } }))
              }
            >
              <option value="control">control</option>
              <option value="variant-A">variant-A</option>
              <option value="variant-B">variant-B</option>
            </Select>
          </div>

          <div className="space-y-1">
            <div className="text-sm font-semibold text-gray-900 dark:text-white">Feature toggles</div>
            {BOOL_FEATURE_KEYS.map(({ key, label }) => (
              <label key={key} className="flex items-center gap-2 text-sm text-gray-700 dark:text-dark-100">
                <input
                  type="checkbox"
                  checked={form.features[key]}
                  onChange={(event) =>
                    setForm((prev) => ({
                      ...prev,
                      features: { ...prev.features, [key]: event.target.checked },
                    }))
                  }
                />
                <span>{label}</span>
              </label>
            ))}
          </div>
        </div>
      </Drawer>
    </div>
  );
}

function MetricCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <Card className="p-5">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-50 text-primary-600 dark:bg-primary-500/10 dark:text-primary-200">
          {icon}
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-dark-200">{label}</div>
          <div className="text-xl font-semibold text-gray-900 dark:text-white">{value}</div>
        </div>
      </div>
    </Card>
  );
}
