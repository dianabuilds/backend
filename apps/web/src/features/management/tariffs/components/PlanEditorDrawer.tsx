import React from 'react';
import {
  Badge,
  Button,
  Card,
  Drawer,
  Input,
  Select,
  Spinner,
  Tabs,
  Textarea,
} from '@ui';

import type { BillingPlanHistoryItem } from '@shared/types/management';

import {
  BOOL_FEATURE_KEYS,
  LIMIT_KEYS,
  PlanFormState,
  PlanTabKey,
  PlanFormFeatures,
  formatHistoryEntry,
} from './helpers';

type PlanEditorDrawerProps = {
  open: boolean;
  saving: boolean;
  form: PlanFormState;
  error: string | null;
  history: BillingPlanHistoryItem[];
  historyLoading: boolean;
  onClose: () => void;
  onChange: (updater: (form: PlanFormState) => PlanFormState) => void;
  onSave: () => Promise<void>;
  onLoadHistory: () => Promise<void>;
  initialTab?: PlanTabKey;
};

const TAB_ITEMS: Array<{ key: PlanTabKey; label: string }> = [
  { key: 'general', label: 'Общие' },
  { key: 'limits', label: 'Лимиты' },
  { key: 'features', label: 'Особенности' },
  { key: 'history', label: 'История' },
  { key: 'preview', label: 'Предпросмотр' },
];

export const PlanEditorDrawer: React.FC<PlanEditorDrawerProps> = ({
  open,
  saving,
  form,
  error,
  history,
  historyLoading,
  onClose,
  onChange,
  onSave,
  onLoadHistory,
  initialTab = 'general',
}) => {
  const [tab, setTab] = React.useState<PlanTabKey>(initialTab);

  React.useEffect(() => {
    if (!open) {
      setTab(initialTab);
    }
  }, [initialTab, open]);

  React.useEffect(() => {
    if (tab === 'history') {
      void onLoadHistory();
    }
  }, [tab, onLoadHistory]);

  const updateForm = (partial: Partial<PlanFormState>) => {
    onChange((prev) => ({ ...prev, ...partial }));
  };

  const updateFeatures = (partial: Partial<PlanFormFeatures>) => {
    onChange((prev) => ({
      ...prev,
      features: { ...prev.features, ...partial },
    }));
  };

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={form.id ? 'Редактирование плана' : 'Новый план'}
      widthClass="w-full lg:w-[960px] xl:w-[1080px]"
      footer={
        <div className="flex items-center justify-between gap-2">
          <div className="text-xs text-gray-500">
            Поля помеченные * обязательны. Ошибки бэкенда отображаются отдельно.
          </div>
          <div className="flex items-center gap-2">
            {error ? <span className="text-xs text-rose-500">{error}</span> : null}
            <Button variant="ghost" onClick={onClose}>
              Отмена
            </Button>
            <Button onClick={() => void onSave()} disabled={saving}>
              {saving ? 'Сохранение…' : 'Сохранить'}
            </Button>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <Tabs
          items={TAB_ITEMS}
          value={tab}
          onChange={(key) => setTab(key as PlanTabKey)}
        />

        {tab === 'general' ? (
          <div className="grid gap-4 md:grid-cols-2">
            <Input
              label="Slug*"
              value={form.slug}
              disabled={Boolean(form.id)}
              onChange={(event) => updateForm({ slug: event.target.value })}
              required
            />
            <Input
              label="Название"
              value={form.title}
              onChange={(event) => updateForm({ title: event.target.value })}
            />
            <Textarea
              label="Описание"
              value={form.description}
              onChange={(event) => updateForm({ description: event.target.value })}
              rows={4}
              className="md:col-span-2"
            />
            <Input
              label="Price (cents)"
              value={form.price_cents}
              onChange={(event) => updateForm({ price_cents: event.target.value })}
            />
            <Input
              label="Currency"
              value={form.currency}
              onChange={(event) => updateForm({ currency: event.target.value })}
            />
            <Input
              label="Price token"
              value={form.price_token}
              onChange={(event) => updateForm({ price_token: event.target.value })}
            />
            <Input
              label="Price USD estimate"
              value={form.price_usd_estimate}
              onChange={(event) => updateForm({ price_usd_estimate: event.target.value })}
            />
            <Select
              label="Интервал"
              value={form.billing_interval}
              onChange={(event) => updateForm({ billing_interval: event.target.value })}
            >
              <option value="month">Month</option>
              <option value="year">Year</option>
              <option value="custom">Custom</option>
            </Select>
            <Select
              label="Статус"
              value={form.features.status}
              onChange={(event) => {
                const value = event.target.value;
                updateForm({ is_active: value === 'active' });
                updateFeatures({ status: value });
              }}
            >
              <option value="active">Active</option>
              <option value="hidden">Hidden</option>
              <option value="draft">Draft</option>
              <option value="archived">Archived</option>
            </Select>
            <Input
              label="Порядок отображения"
              value={form.order}
              onChange={(event) => updateForm({ order: event.target.value })}
            />
            <Input
              label="Gateway slug"
              value={form.gateway_slug}
              onChange={(event) => updateForm({ gateway_slug: event.target.value })}
            />
            <Input
              label="Contract slug"
              value={form.contract_slug}
              onChange={(event) => updateForm({ contract_slug: event.target.value })}
            />
          </div>
        ) : null}

        {tab === 'limits' ? (
          <Card className="space-y-3 border border-gray-100 p-4">
            <div className="text-sm font-semibold text-gray-900">Месячные лимиты</div>
            <div className="grid gap-3 md:grid-cols-2">
              {LIMIT_KEYS.map((item) => (
                <Input
                  key={item.key}
                  label={item.label}
                  value={form.monthly_limits[item.key] ?? ''}
                  onChange={(event) =>
                    onChange((prev) => ({
                      ...prev,
                      monthly_limits: {
                        ...prev.monthly_limits,
                        [item.key]: event.target.value,
                      },
                    }))
                  }
                />
              ))}
            </div>
          </Card>
        ) : null}

        {tab === 'features' ? (
          <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              <Select
                label="Аудитория"
                value={form.features.audience}
                onChange={(event) => updateFeatures({ audience: event.target.value })}
              >
                <option value="off">Off</option>
                <option value="all">All</option>
                <option value="premium">Premium</option>
              </Select>
              <Select
                label="A/B вариант"
                value={form.features.ab_variant}
                onChange={(event) => updateFeatures({ ab_variant: event.target.value })}
              >
                <option value="control">Control</option>
                <option value="variant-A">Variant A</option>
                <option value="variant-B">Variant B</option>
              </Select>
              <Input
                label="Пробный период (дней)"
                value={form.features.trial_days}
                onChange={(event) => updateFeatures({ trial_days: event.target.value })}
              />
              <Textarea
                label="Feature flags"
                value={form.features.flags}
                onChange={(event) => updateFeatures({ flags: event.target.value })}
              />
              <Textarea
                label="Allowed models"
                value={form.features.models_allowed}
                onChange={(event) => updateFeatures({ models_allowed: event.target.value })}
              />
            </div>
            <div className="space-y-2">
              <div className="text-sm font-semibold text-gray-900">Функциональные опции</div>
              <div className="grid gap-2 md:grid-cols-2">
                {BOOL_FEATURE_KEYS.map(({ key, label }) => (
                  <label key={key} className="flex items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={Boolean(form.features[key])}
                      onChange={(event) =>
                        updateFeatures({ [key]: event.target.checked } as Partial<PlanFormFeatures>)
                      }
                    />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        ) : null}

        {tab === 'history' ? (
          <Card className="space-y-3 border border-gray-100 p-4">
            {historyLoading ? (
              <div className="flex min-h-[160px] items-center justify-center">
                <Spinner />
              </div>
            ) : history.length === 0 ? (
              <div className="text-sm text-gray-500">История изменений ещё не зафиксирована.</div>
            ) : (
              <div className="space-y-3">
                {history.map((item) => {
                  const entry = formatHistoryEntry(item);
                  return (
                    <Card key={entry.id} className="border border-gray-200 p-3 text-xs">
                      <div className="flex items-center justify-between">
                        <div className="font-semibold text-gray-700">{entry.action}</div>
                        <div className="text-gray-500">{entry.actor}</div>
                      </div>
                      <div className="mt-1 text-gray-500">
                        {entry.created_at ? new Date(entry.created_at).toLocaleString() : '—'}
                      </div>
                      <pre className="mt-2 max-h-40 overflow-auto rounded bg-gray-50 p-2">
                        {JSON.stringify(entry.payload, null, 2)}
                      </pre>
                    </Card>
                  );
                })}
              </div>
            )}
          </Card>
        ) : null}

        {tab === 'preview' ? (
          <Card className="space-y-3 border border-gray-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-lg font-semibold text-gray-900">{form.title || form.slug || 'Plan name'}</div>
                <div className="text-sm text-gray-500">{form.description || 'Описание будет отображаться здесь.'}</div>
              </div>
              <Badge color={form.is_active ? 'success' : 'neutral'}>
                {form.is_active ? 'Active' : 'Hidden'}
              </Badge>
            </div>
            <div className="text-sm text-gray-700">
              <span className="text-2xl font-semibold text-gray-900">{centsToUsd(form.price_cents)}</span>
              <span className="ml-2 text-gray-500">/ {form.billing_interval}</span>
            </div>
            <div className="grid gap-2 text-xs text-gray-600 md:grid-cols-2">
              {LIMIT_KEYS.map((item) => (
                <div key={item.key}>
                  <span className="font-semibold text-gray-700">{item.label}:</span>{' '}
                  <span>{form.monthly_limits[item.key] || '—'}</span>
                </div>
              ))}
            </div>
            <div className="text-xs text-gray-500">
              Audience: {form.features.audience || 'off'} | AB Variant: {form.features.ab_variant}
            </div>
          </Card>
        ) : null}
      </div>
    </Drawer>
  );
};

function centsToUsd(value: string) {
  const num = Number(value);
  if (Number.isNaN(num)) return '—';
  return '$' + (num / 100).toFixed(2);
}
