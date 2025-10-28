import React from 'react';
import { Button, Card, Input, Table } from '@ui';

import type { BillingPlan, BillingPlanLimitsUpdate } from '@shared/types/management';

import { LIMIT_KEYS } from './helpers';

type LimitsMatrixProps = {
  plans: BillingPlan[];
  saving: boolean;
  onSave: (updates: BillingPlanLimitsUpdate[]) => Promise<void>;
};

type DraftState = Record<string, Record<string, string>>;

export const LimitsMatrix: React.FC<LimitsMatrixProps> = ({ plans, saving, onSave }) => {
  const [draft, setDraft] = React.useState<DraftState>(() => buildInitialDraft(plans));
  const [dirty, setDirty] = React.useState<Record<string, Set<string>>>(() => ({}));

  React.useEffect(() => {
    setDraft(buildInitialDraft(plans));
    setDirty({});
  }, [plans]);

  const handleChange = (planSlug: string, limitKey: string, value: string) => {
    setDraft((prev) => ({
      ...prev,
      [planSlug]: {
        ...prev[planSlug],
        [limitKey]: value,
      },
    }));
    setDirty((prev) => {
      const next = { ...prev };
      if (!next[planSlug]) next[planSlug] = new Set<string>();
      next[planSlug].add(limitKey);
      return next;
    });
  };

  const handleSave = async () => {
    const updates: BillingPlanLimitsUpdate[] = Object.entries(draft).map(([slug, limits]) => {
      const sanitized: Record<string, unknown> = {};
      Object.entries(limits).forEach(([key, value]) => {
        const parsed = Number.parseInt(value.trim(), 10);
        if (!Number.isNaN(parsed)) {
          sanitized[key] = parsed;
        }
      });
      return { slug, monthly_limits: sanitized };
    });
    await onSave(updates);
    setDirty({});
  };

  return (
    <Card className="space-y-4 p-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Матричное редактирование лимитов</h2>
          <p className="text-sm text-gray-500">
            Изменённые ячейки подсвечиваются. Пустое значение оставляет лимит без изменений.
          </p>
        </div>
        <Button size="sm" onClick={() => void handleSave()} disabled={saving}>
          {saving ? 'Сохранение…' : 'Сохранить изменения'}
        </Button>
      </div>

      <div className="overflow-x-auto">
        <Table.Table className="min-w-[960px] text-sm">
          <Table.THead>
            <Table.TR>
              <Table.TH>План</Table.TH>
              {LIMIT_KEYS.map((item) => (
                <Table.TH key={item.key}>{item.label}</Table.TH>
              ))}
            </Table.TR>
          </Table.THead>
          <Table.TBody>
            {plans.map((plan) => (
              <Table.TR key={plan.slug}>
                <Table.TD className="font-semibold text-gray-900">
                  {plan.title || plan.slug}
                </Table.TD>
                {LIMIT_KEYS.map((item) => {
                  const value = draft[plan.slug]?.[item.key] ?? '';
                  const isDirty = dirty[plan.slug]?.has(item.key);
                  return (
                    <Table.TD key={item.key}>
                      <Input
                        value={value}
                        onChange={(event) => handleChange(plan.slug, item.key, event.target.value)}
                        className={isDirty ? 'border-primary-300 bg-primary-50' : ''}
                        placeholder={String(
                          (plan.monthly_limits && plan.monthly_limits[item.key]) ?? '',
                        )}
                      />
                    </Table.TD>
                  );
                })}
              </Table.TR>
            ))}
          </Table.TBody>
        </Table.Table>
      </div>
    </Card>
  );
};

function buildInitialDraft(plans: BillingPlan[]): DraftState {
  const draft: DraftState = {};
  plans.forEach((plan) => {
    const limits =
      plan.monthly_limits && typeof plan.monthly_limits === 'object'
        ? plan.monthly_limits
        : {};
    draft[plan.slug] = LIMIT_KEYS.reduce<Record<string, string>>((acc, item) => {
      const value = limits[item.key];
      acc[item.key] = value != null ? String(value) : '';
      return acc;
    }, {});
  });
  return draft;
}
