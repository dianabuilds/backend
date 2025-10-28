import type { Meta, StoryObj } from '@storybook/react';

import { PlansCatalog, type PlanFilters } from './PlansCatalog';

const meta: Meta<typeof PlansCatalog> = {
  title: 'Management/Billing/PlansCatalog',
  component: PlansCatalog,
  parameters: {
    layout: 'padded',
  },
};

export default meta;

type Story = StoryObj<typeof PlansCatalog>;

const plansSample = [
  {
    id: 'plan-starter',
    slug: 'starter',
    title: 'Starter',
    description: 'Для команд, которые пробуют платформу.',
    price_cents: 9900,
    currency: 'USD',
    price_token: 'USDC',
    price_usd_estimate: 99,
    billing_interval: 'month',
    is_active: true,
    order: 1,
    gateway_slug: 'stripe-main',
    contract_slug: 'main-vault',
    monthly_limits: {
      api_quota: 100000,
      llm_tokens_month: 1500000,
      quest_generations: 500,
    },
    features: {
      status: 'active',
      audience: 'all',
      ab_variant: 'control',
    },
  },
  {
    id: 'plan-growth',
    slug: 'growth',
    title: 'Growth',
    description: 'Расширенные лимиты и приоритетная поддержка.',
    price_cents: 29900,
    currency: 'USD',
    price_token: 'USDC',
    price_usd_estimate: 299,
    billing_interval: 'month',
    is_active: true,
    order: 2,
    gateway_slug: 'stripe-main',
    contract_slug: 'main-vault',
    monthly_limits: {
      api_quota: 500000,
      llm_tokens_month: 4000000,
      quest_generations: 2000,
    },
    features: {
      status: 'active',
      audience: 'premium',
      ab_variant: 'variant-A',
      compass_enhanced: true,
    },
  },
  {
    id: 'plan-enterprise',
    slug: 'enterprise',
    title: 'Enterprise',
    description: 'Настраиваемые лимиты, SLA и выделенный менеджер.',
    price_cents: null,
    currency: 'USD',
    price_token: 'USDC',
    price_usd_estimate: null,
    billing_interval: 'custom',
    is_active: false,
    order: 3,
    gateway_slug: 'manual',
    contract_slug: 'enterprise-deal',
    monthly_limits: {},
    features: {
      status: 'draft',
      audience: 'off',
      ab_variant: 'control',
    },
  },
] as any;

const defaultFilters: PlanFilters = {
  search: '',
  status: 'all',
  interval: 'all',
  token: '',
};

export const Default: Story = {
  args: {
    plans: plansSample,
    filters: defaultFilters,
    onChangeFilters: () => undefined,
    onCreate: () => undefined,
    onEdit: () => undefined,
    onHistory: () => undefined,
    onDelete: () => undefined,
  },
};

