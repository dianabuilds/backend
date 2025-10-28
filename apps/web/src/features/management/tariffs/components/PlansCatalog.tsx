import React from 'react';
import { Badge, Button, Card, Input, Select } from '@ui';

import type { BillingPlan } from '@shared/types/management';

export type PlanFilters = {
  search: string;
  status: 'all' | 'active' | 'hidden' | 'draft';
  interval: 'all' | 'month' | 'year' | 'custom';
  token: string;
};

type PlansCatalogProps = {
  plans: BillingPlan[];
  filters: PlanFilters;
  onChangeFilters: (filters: PlanFilters) => void;
  onCreate: () => void;
  onEdit: (plan: BillingPlan) => void;
  onHistory: (plan: BillingPlan) => void;
  onDelete: (plan: BillingPlan) => void;
};

const matchFilters = (plan: BillingPlan, filters: PlanFilters) => {
  if (filters.search.trim()) {
    const query = filters.search.trim().toLowerCase();
    const haystack = `${plan.title ?? ''} ${plan.slug}`.toLowerCase();
    if (!haystack.includes(query)) return false;
  }
  if (filters.status === 'active' && !plan.is_active) return false;
  if (filters.status === 'hidden' && plan.is_active) return false;
  if (filters.status === 'draft') {
    const features = plan.features && typeof plan.features === 'object' ? plan.features : {};
    const status = String(features.status ?? (plan.is_active ? 'active' : 'draft')).toLowerCase();
    if (status !== 'draft') return false;
  }
  if (filters.interval !== 'all') {
    const interval = String(plan.billing_interval ?? 'month');
    if (interval !== filters.interval) return false;
  }
  if (filters.token.trim()) {
    const token = plan.price_token ?? plan.currency ?? '';
    if (!token.toLowerCase().includes(filters.token.toLowerCase())) return false;
  }
  return true;
};

export const PlansCatalog: React.FC<PlansCatalogProps> = ({
  plans,
  filters,
  onChangeFilters,
  onCreate,
  onEdit,
  onHistory,
  onDelete,
}) => {
  const filteredPlans = React.useMemo(
    () => plans.filter((plan) => matchFilters(plan, filters)),
    [plans, filters],
  );

  const tokens = React.useMemo(() => {
    const set = new Set<string>();
    plans.forEach((plan) => {
      const token = plan.price_token ?? plan.currency;
      if (token) set.add(token);
    });
    return Array.from(set).sort();
  }, [plans]);

  return (
    <Card className="space-y-5 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Тарифные планы</h2>
          <p className="text-sm text-gray-500">
            Быстрый просмотр ключевых лимитов и статус плана. Используйте фильтры для выделения целевой группы.
          </p>
        </div>
        <Button size="sm" onClick={onCreate}>
          Новый план
        </Button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Input
          label="Поиск"
          placeholder="Название или slug"
          value={filters.search}
          onChange={(event) => onChangeFilters({ ...filters, search: event.target.value })}
        />
        <Select
          label="Статус"
          value={filters.status}
          onChange={(event) =>
            onChangeFilters({ ...filters, status: event.target.value as PlanFilters['status'] })
          }
        >
          <option value="all">Все</option>
          <option value="active">Активные</option>
          <option value="hidden">Скрытые</option>
          <option value="draft">Черновики</option>
        </Select>
        <Select
          label="Интервал"
          value={filters.interval}
          onChange={(event) =>
            onChangeFilters({ ...filters, interval: event.target.value as PlanFilters['interval'] })
          }
        >
          <option value="all">Любой</option>
          <option value="month">Monthly</option>
          <option value="year">Yearly</option>
          <option value="custom">Custom</option>
        </Select>
        <Select
          label="Валюта/Токен"
          value={filters.token}
          onChange={(event) => onChangeFilters({ ...filters, token: event.target.value })}
        >
          <option value="">Все</option>
          {tokens.map((token) => (
            <option key={token} value={token}>
              {token}
            </option>
          ))}
        </Select>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filteredPlans.map((plan) => {
          const features =
            plan.features && typeof plan.features === 'object'
              ? plan.features
              : {};
          const status = String(features.status ?? (plan.is_active ? 'active' : 'draft'));
          const audience = String(features.audience ?? 'off');
          const interval = String(plan.billing_interval ?? 'month');
          const token = plan.price_token ?? plan.currency ?? 'USD';
          const limitsSummary = Object.entries(plan.monthly_limits || {})
            .slice(0, 3)
            .map(([key, value]) => `${key}: ${value}`)
            .join(', ');

          return (
            <Card key={plan.id} className="flex flex-col gap-3 border border-gray-100 p-4 shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-sm font-semibold text-gray-900">{plan.title || plan.slug}</div>
                  <div className="text-xs text-gray-500">Slug: {plan.slug}</div>
                </div>
                <Badge color={plan.is_active ? 'success' : 'neutral'}>
                  {plan.is_active ? 'Active' : 'Hidden'}
                </Badge>
              </div>
              <div className="text-sm text-gray-700 line-clamp-2">{plan.description || '—'}</div>
              <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
                <Badge color="primary">{interval}</Badge>
                <Badge color="neutral">{token}</Badge>
                <Badge color="neutral">Audience: {audience}</Badge>
                <Badge color={status === 'draft' ? 'warning' : 'neutral'}>Status: {status}</Badge>
              </div>
              <div className="text-sm">
                <span className="font-semibold text-gray-900">{centsToUsd(plan.price_cents)}</span>
                <span className="text-gray-500"> / {interval}</span>
              </div>
              <div className="min-h-[40px] text-xs text-gray-500">
                {limitsSummary || 'Лимиты не настроены'}
              </div>
              <div className="mt-auto flex items-center gap-2">
                <Button size="sm" variant="ghost" onClick={() => onEdit(plan)}>
                  Редактировать
                </Button>
                <Button size="sm" variant="ghost" onClick={() => onHistory(plan)}>
                  История
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  color="error"
                  onClick={() => onDelete(plan)}
                >
                  Удалить
                </Button>
              </div>
            </Card>
          );
        })}

        {filteredPlans.length === 0 ? (
          <Card className="col-span-full p-6 text-center text-sm text-gray-500">
            Под подходящие фильтры не найдено планов.
          </Card>
        ) : null}
      </div>
    </Card>
  );
};

function centsToUsd(value?: number | null) {
  if (typeof value !== 'number') return '—';
  return '$' + (value / 100).toFixed(2);
}
