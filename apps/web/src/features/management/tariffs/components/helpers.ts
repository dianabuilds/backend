import type {
  BillingPlan,
  BillingPlanPayload,
  BillingPlanHistoryItem,
} from '@shared/types/management';

export type PlanTabKey = 'general' | 'limits' | 'features' | 'history' | 'preview';

export type PlanFormFeatures = {
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

export const LIMIT_KEYS: Array<{ key: string; label: string }> = [
  { key: 'llm_tokens_month', label: 'LLM tokens / month' },
  { key: 'quest_generations', label: 'Quest generations' },
  { key: 'echo_traces', label: 'Echo traces' },
  { key: 'tag_notifications', label: 'Tag notifications' },
  { key: 'worlds_max', label: 'Worlds max' },
  { key: 'nodes_max', label: 'Nodes max' },
  { key: 'transitions_max', label: 'Transitions max' },
  { key: 'api_quota', label: 'API quota' },
];

export const BOOL_FEATURE_KEYS: Array<{ key: keyof PlanFormFeatures; label: string }> = [
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

export type PlanFormState = {
  id?: string;
  slug: string;
  title: string;
  description: string;
  price_cents: string;
  currency: string;
  price_token: string;
  price_usd_estimate: string;
  billing_interval: string;
  is_active: boolean;
  order: string;
  gateway_slug: string;
  contract_slug: string;
  monthly_limits: Record<string, string>;
  features: PlanFormFeatures;
};

export const DEFAULT_PLAN_FORM: PlanFormState = {
  slug: '',
  title: '',
  description: '',
  price_cents: '',
  currency: 'USD',
  price_token: '',
  price_usd_estimate: '',
  billing_interval: 'month',
  is_active: false,
  order: '',
  gateway_slug: '',
  contract_slug: '',
  monthly_limits: LIMIT_KEYS.reduce<Record<string, string>>((acc, item) => {
    acc[item.key] = '';
    return acc;
  }, {}),
  features: { ...DEFAULT_FEATURES },
};

export const createFormFromPlan = (plan: BillingPlan): PlanFormState => {
  const limits =
    plan.monthly_limits && typeof plan.monthly_limits === 'object'
      ? plan.monthly_limits
      : {};
  const features =
    plan.features && typeof plan.features === 'object'
      ? plan.features
      : {};

  return {
    id: plan.id,
    slug: plan.slug,
    title: plan.title ?? '',
    description: plan.description ?? '',
    price_cents: plan.price_cents != null ? String(plan.price_cents) : '',
    currency: plan.currency ?? 'USD',
    price_token: plan.price_token ?? '',
    price_usd_estimate:
      plan.price_usd_estimate != null ? String(plan.price_usd_estimate) : '',
    billing_interval: plan.billing_interval ?? 'month',
    is_active: Boolean(plan.is_active),
    order: plan.order != null ? String(plan.order) : '',
    gateway_slug: plan.gateway_slug ?? '',
    contract_slug: plan.contract_slug ?? '',
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
};

const parseIntOrNull = (value: string): number | null => {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number.parseInt(trimmed, 10);
  return Number.isNaN(parsed) ? null : parsed;
};

const parseFloatOrNull = (value: string): number | null => {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number.parseFloat(trimmed);
  return Number.isNaN(parsed) ? null : parsed;
};

const parseNumber = (value: string): number | null => {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Number(trimmed);
  return Number.isNaN(parsed) ? null : parsed;
};

export const buildPlanPayload = (form: PlanFormState): BillingPlanPayload | null => {
  const slug = form.slug.trim();
  if (!slug) {
    return null;
  }
  const price = parseNumber(form.price_cents);
  const order = parseIntOrNull(form.order);
  const usdEstimate = parseFloatOrNull(form.price_usd_estimate);

  const monthlyLimits: Record<string, unknown> = {};
  Object.entries(form.monthly_limits).forEach(([key, value]) => {
    const parsed = parseIntOrNull(value);
    if (parsed != null) {
      monthlyLimits[key] = parsed;
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
    const featureKey = key as keyof PlanFormFeatures;
    features[featureKey] = form.features[featureKey];
  });

  const payload: BillingPlanPayload = {
    id: form.id,
    slug,
    title: form.title.trim() || undefined,
    description: form.description.trim() || undefined,
    currency: form.currency.trim() || undefined,
    price_cents: price ?? null,
    price_token: form.price_token.trim() || undefined,
    price_usd_estimate: form.price_usd_estimate.trim()
      ? usdEstimate ?? null
      : undefined,
    billing_interval: form.billing_interval || undefined,
    is_active: form.is_active,
    order: order ?? undefined,
    gateway_slug: form.gateway_slug.trim() || undefined,
    contract_slug: form.contract_slug.trim() || undefined,
    monthly_limits: Object.keys(monthlyLimits).length ? monthlyLimits : null,
    features: Object.keys(features).length ? features : null,
  };

  return payload;
};

export const countExperiments = (plans: BillingPlan[]) => {
  let experiments = 0;
  let activeExperiments = 0;

  plans.forEach((plan) => {
    const features =
      plan.features && typeof plan.features === 'object'
        ? plan.features
        : {};
    const variant = String(features.ab_variant ?? 'control');
    if (variant !== 'control') {
      experiments += 1;
      if (plan.is_active) activeExperiments += 1;
    }
  });

  return { experiments, activeExperiments };
};

export const formatHistoryEntry = (item: BillingPlanHistoryItem) => ({
  id: item.id || `${item.action}-${item.created_at}`,
  action: item.action || 'update',
  actor: item.actor || '—',
  created_at: item.created_at,
  payload: item.payload || {},
});
